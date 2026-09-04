"""Generate the derived print assets for the certificate designs.

Two jobs, both deterministic, both committed as PNGs:

* Guilloche. WeasyPrint has no repeating or conic gradients, and the fine
  interlaced line work that makes a certificate look engraved cannot be faked
  with borders, so the rosette and the border braid are drawn here.
* Transparent logos. The source logos are opaque RGB, which paints a white
  rectangle over ivory stock or a green panel. These key the white out.

    python manage.py build_certificate_assets

Re-run only when the artwork or the source logos change.
"""

import math
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

SUPERSAMPLE = 4


class Command(BaseCommand):
    help = 'Redraw the certificate guilloche artwork and the transparent logo variants.'

    def handle(self, *args, **options):
        from PIL import Image, ImageDraw

        out_dir = Path(settings.BASE_DIR) / 'static' / 'certificates'
        out_dir.mkdir(parents=True, exist_ok=True)

        self._rosette(Image, ImageDraw, 1100).save(out_dir / 'guilloche_rosette.png')
        self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / "guilloche_rosette.png"}'))

        self._border(Image, ImageDraw, 1200, 90).save(out_dir / 'guilloche_border.png')
        self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / "guilloche_border.png"}'))

        for source, target in (('headerlogo.png', 'headerlogo_alpha.png'),
                               ('footer_right_logo.png', 'footer_right_logo_alpha.png')):
            self._keyed_out(Image, out_dir / source).save(out_dir / target)
            self.stdout.write(self.style.SUCCESS(f'wrote {out_dir / target}'))

    def _rosette(self, Image, ImageDraw, size):
        """Nested epitrochoids - the spirograph rosette on banknotes and share certificates."""
        s = size * SUPERSAMPLE
        img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = cy = s / 2
        width = max(1, SUPERSAMPLE)

        # Each ring is one epitrochoid; stepping the phase makes them interlace.
        for ring, (radius, petals, depth) in enumerate((
            (0.455, 48, 0.028),
            (0.400, 36, 0.032),
            (0.345, 60, 0.020),
            (0.280, 30, 0.026),
            (0.215, 42, 0.018),
            (0.145, 24, 0.022),
            (0.080, 18, 0.016),
        )):
            R = radius * s
            r = depth * s
            for phase_step in range(3):
                phase = phase_step * (2 * math.pi / 3) / petals
                points = []
                for i in range(2400):
                    t = i * 2 * math.pi / 2400 + phase
                    points.append((
                        cx + R * math.cos(t) + r * math.cos(petals * t),
                        cy + R * math.sin(t) + r * math.sin(petals * t),
                    ))
                points.append(points[0])
                alpha = 200 - ring * 10
                draw.line(points, fill=(20, 65, 47, alpha), width=width, joint='curve')

        # A plain hairline circle to close the outside edge.
        pad = 0.035 * s
        draw.ellipse((pad, pad, s - pad, s - pad), outline=(20, 65, 47, 150), width=width)

        return img.resize((size, size), Image.LANCZOS)

    def _border(self, Image, ImageDraw, width, height):
        """A braid of phase-shifted sine waves, tileable left to right."""
        w, h = width * SUPERSAMPLE, height * SUPERSAMPLE
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        line_w = max(1, SUPERSAMPLE)

        # 6 whole cycles across the tile keeps the seam invisible when repeated.
        cycles = 6
        for strand in range(5):
            phase = strand * math.pi / 5
            amp = h * (0.36 - strand * 0.030)
            points = []
            for x in range(w + 1):
                t = x / w * cycles * 2 * math.pi
                y = h / 2 + amp * math.sin(t + phase) + amp * 0.35 * math.sin(3 * t - phase)
                points.append((x, y))
            draw.line(points, fill=(20, 65, 47, 165), width=line_w, joint='curve')

        return img.resize((width, height), Image.LANCZOS)

    @staticmethod
    def _keyed_out(Image, path, threshold=238):
        """Drop the white background so the mark can sit on tinted stock.

        Near-white pixels fade out proportionally rather than snapping to
        transparent, which keeps the antialiased edges of the type clean.
        """
        img = Image.open(path).convert('RGBA')
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
