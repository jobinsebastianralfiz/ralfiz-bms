"""Generate the derived print assets for the certificate designs.

Everything here exists because WeasyPrint cannot compute it at render time.
All of it is deterministic and committed as PNGs:

* The certificate background. The design layers blurred radial glows over a
  linear gradient, and WeasyPrint has no `filter: blur()`, so the whole field
  is baked into one image.
* White logo, signature and seal. The design applies `brightness(0) invert(1)`
  and `invert(1)` to drop them onto the dark ground; those filters are not
  supported either, so the inverted variants are made here.
* Transparent logos - the source lockups are opaque RGB and would otherwise
  paint a white rectangle wherever the ground is not white.

    python manage.py build_certificate_assets

Re-run only when the artwork or the source logos change.
"""

import math
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Redraw the certificate background and the white/transparent logo variants.'

    def handle(self, *args, **options):
        from PIL import Image

        out_dir = Path(settings.BASE_DIR) / 'static' / 'certificates'
        out_dir.mkdir(parents=True, exist_ok=True)

        for source, target in (('headerlogo.png', 'headerlogo_alpha.png'),
                               ('footer_right_logo.png', 'footer_right_logo_alpha.png')):
            self._keyed_out(Image, out_dir / source).save(out_dir / target)
            self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / target}'))

        # White-on-dark variants for the navy design. That design sets the
        # company name in Poppins beside the RT mark alone, so the wordmark
        # baked into the source lockup has to be cut away first.
        self._to_white(Image, out_dir / 'headerlogo_alpha.png').save(out_dir / 'headerlogo_white.png')
        self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / "headerlogo_white.png"}'))
        mark = self._to_white(Image, out_dir / 'headerlogo_alpha.png')
        self._first_glyph_group(Image, mark).save(out_dir / 'rt_mark_white.png')
        self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / "rt_mark_white.png"}'))
        for source, target in (('jobin_signature.png', 'jobin_signature_white.png'),
                               ('seal.png', 'seal_white.png')):
            self._inverted(Image, self._keyed_out(Image, out_dir / source)).save(out_dir / target)
            self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / target}'))

        self._background(Image, 1122, 794).save(out_dir / 'certificate_bg.png')
        self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / "certificate_bg.png"}'))

    @staticmethod
    def _open(Image, source):
        return source.convert('RGBA') if hasattr(source, 'convert') else Image.open(source).convert('RGBA')

    @classmethod
    def _first_glyph_group(cls, Image, img):
        """Crop to the first cluster of ink, i.e. the RT mark on its own.

        The lockup is mark + gap + wordmark, so the first run of blank
        columns wide enough to be a word space marks the cut.
        """
        w, h = img.size
        px = img.load()
        ink = [any(px[x, y][3] > 24 for y in range(h)) for x in range(w)]

        cut = w
        run = 0
        for x in range(w):
            if ink[x]:
                if run >= 8 and any(ink[:x]):
                    cut = x - run
                    break
                run = 0
            else:
                run += 1

        rows = [y for y in range(h) if any(px[x, y][3] > 24 for x in range(cut))]
        left = next(x for x in range(cut) if ink[x])
        return img.crop((left, rows[0], cut, rows[-1] + 1))

    @classmethod
    def _keyed_out(cls, Image, source, threshold=238):
        """Drop the white background so the mark can sit on tinted stock.

        Near-white pixels fade out proportionally rather than snapping to
        transparent, which keeps the antialiased edges of the type clean.
        """
        img = cls._open(Image, source)
        pixels = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                lightest = max(r, g, b)
                if lightest < threshold:
                    continue
                darkest = min(r, g, b)
                # Coloured pixels stay; only near-greys near white go.
                if lightest - darkest > 18:
                    continue
                pixels[x, y] = (r, g, b, int(a * (255 - lightest) / (255 - threshold)))
        return img

    @classmethod
    def _to_white(cls, Image, source):
        """`filter: brightness(0) invert(1)` - a white silhouette, alpha kept."""
        img = cls._open(Image, source)
        r, g, b, a = img.split()
        white = Image.new('L', img.size, 255)
        return Image.merge('RGBA', (white, white, white, a))

    @classmethod
    def _inverted(cls, Image, source):
        """`filter: invert(1)` - black ink becomes white, alpha kept."""
        from PIL import ImageChops
        img = cls._open(Image, source)
        r, g, b, a = img.split()
        rgb = Image.merge('RGB', (r, g, b))
        r, g, b = ImageChops.invert(rgb).split()
        return Image.merge('RGBA', (r, g, b, a))

    def _background(self, Image, width, height, scale=3):
        """The navy field: a linear gradient under four blurred radial glows.

        Sizes are the design's CSS pixels; `scale` renders above print
        resolution so the gradient does not band on paper.
        """
        import numpy as np
        from PIL import ImageFilter

        w, h = width * scale, height * scale
        base = self._linear_gradient(
            np, w, h, 115,
            [(0.00, (0x0a, 0x0d, 0x3d)), (0.32, (0x0b, 0x13, 0x50)),
             (0.62, (0x12, 0x2a, 0x9c)), (1.00, (0x1b, 0x47, 0xd8))])
        canvas = Image.fromarray(base, 'RGB').convert('RGBA')

        # (left, top, w, h, stops, blur, opacity) in design pixels.
        glows = [
            (-190, -160, 520, 430,
             [(0.00, (0xe3, 0xa8, 0xf5), 1.0), (0.45, (0xa4, 0x63, 0xe8), 1.0), (0.78, (90, 40, 180), 0.0)],
             28, 0.92),
            (-60, 120, 300, 260,
             [(0.00, (0x1a, 0x1f, 0x6e), 1.0), (0.72, (0x0a, 0x0d, 0x3d), 0.0)],
             24, 1.0),
            (width - 320 + 320 - 540 + 320, height - 60 - 430, 540, 430,
             [(0.00, (0xe6, 0xcf, 0xe8), 1.0), (0.44, (0xb6, 0xa6, 0xea), 1.0), (0.76, (90, 80, 220), 0.0)],
             34, 0.62),
        ]
        # The third glow is anchored bottom:60 right:-320, i.e. its left edge
        # sits 320px past the right trim.
        glows[2] = (width - 220, height - 490, 540, 430, glows[2][4], 34, 0.62)
        # The second is top:-60 left:120.
        glows[1] = (120, -60, 300, 260, glows[1][4], 24, 1.0)

        for left, top, gw, gh, stops, blur, opacity in glows:
            layer = Image.fromarray(
                self._radial_glow(np, w, h,
                                  left * scale, top * scale, gw * scale, gh * scale, stops),
                'RGBA')
            layer = layer.filter(ImageFilter.GaussianBlur(blur * scale))
            if opacity < 1.0:
                alpha = layer.getchannel('A').point(lambda v: int(v * opacity))
                layer.putalpha(alpha)
            canvas = Image.alpha_composite(canvas, layer)

        # Scrim along the foot so the footer type keeps its contrast.
        scrim = self._vertical_scrim(np, w, h, 190 * scale,
                                     [(0.00, 0.90), (0.45, 0.62), (1.00, 0.0)], (6, 9, 42))
        canvas = Image.alpha_composite(canvas, Image.fromarray(scrim, 'RGBA'))

        return canvas.convert('RGB').resize((width * 2, height * 2), Image.LANCZOS)

    @staticmethod
    def _linear_gradient(np, w, h, angle_deg, stops):
        """CSS `linear-gradient(<angle>, ...)`: 0deg points up, clockwise."""
        a = math.radians(angle_deg)
        dx, dy = math.sin(a), -math.cos(a)
        length = abs(w * math.sin(a)) + abs(h * math.cos(a))
        ys, xs = np.mgrid[0:h, 0:w]
        t = (((xs - w / 2) * dx + (ys - h / 2) * dy) / length + 0.5).clip(0, 1)

        positions = np.array([p for p, _ in stops])
        colours = np.array([c for _, c in stops], dtype=float)
        out = np.zeros((h, w, 3))
        for channel in range(3):
            out[:, :, channel] = np.interp(t, positions, colours[:, channel])
        return out.astype('uint8')

    @staticmethod
    def _radial_glow(np, w, h, left, top, gw, gh, stops):
        """CSS `radial-gradient(closest-side, ...)` inside a `border-radius:50%` box."""
        cx, cy = left + gw / 2, top + gh / 2
        ys, xs = np.mgrid[0:h, 0:w]
        t = np.sqrt(((xs - cx) / (gw / 2)) ** 2 + ((ys - cy) / (gh / 2)) ** 2).clip(0, 1)

        positions = np.array([p for p, _, _ in stops])
        colours = np.array([c for _, c, _ in stops], dtype=float)
        alphas = np.array([a for _, _, a in stops], dtype=float)

        out = np.zeros((h, w, 4))
        for channel in range(3):
            out[:, :, channel] = np.interp(t, positions, colours[:, channel])
        out[:, :, 3] = np.interp(t, positions, alphas) * 255
        # closest-side stops painting past the ellipse.
        out[:, :, 3] *= (t < 1.0)
        return out.astype('uint8')

    @staticmethod
    def _vertical_scrim(np, w, h, band, stops, colour):
        """`linear-gradient(to top, ...)` over the bottom `band` pixels."""
        out = np.zeros((h, w, 4))
        out[:, :, 0], out[:, :, 1], out[:, :, 2] = colour
        ys = np.arange(h)
        # 0 at the very bottom, 1 at the top of the band.
        t = ((h - 1 - ys) / band).clip(0, 1)
        positions = np.array([p for p, _ in stops])
        alphas = np.array([a for _, a in stops], dtype=float)
        out[:, :, 3] = np.interp(t, positions, alphas)[:, None] * 255
        return out.astype('uint8')
