/* ==========================================================================
   PULSE detail stage

   Drives the command-centre look on client/project detail pages: the record
   is an animated orb at the centre of the stage, and bezier tendrils reach
   out to every floating panel. Adapted from pulse.js (command centre) with
   the orb tinted by the record's status hue instead of fixed violet.

   Expects: #pulse-stage[data-status], #stage-orb (square canvas),
   #stage-field (overlay canvas), and .stage-panel sections.
   ========================================================================== */

(function () {
  'use strict';

  var stage = document.getElementById('pulse-stage');
  var orbCanvas = document.getElementById('stage-orb');
  var fieldCanvas = document.getElementById('stage-field');
  if (!stage || !orbCanvas) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var panels = Array.prototype.slice.call(stage.querySelectorAll('.stage-panel'));

  /* ── Collapsible facets ─────────────────────────────────────────── */
  /* Every panel starts as a compact chip; its kicker toggles the body.
     Choices persist per panel title. The record's primary dossier
     (project info / contact info) starts open. */

  var firstLeft = stage.querySelector('.sp-dossier, .sp-col-l');
  panels.forEach(function (panel) {
    var kicker = panel.querySelector('.stage-panel__kicker');
    if (!kicker) {
      var title = panel.querySelector('.card-title');
      kicker = document.createElement('h2');
      kicker.className = 'stage-panel__kicker';
      kicker.textContent = title ? title.textContent.trim() : 'Details';
      panel.insertBefore(kicker, panel.firstChild);
      // The kicker now names the panel; the first card repeating it is noise.
      if (title) {
        var header = title.closest('.card-header');
        if (header) header.style.display = 'none';
      }
    }
    var key = 'pulseStage.' + kicker.textContent.trim();

    var chev = document.createElement('span');
    chev.className = 'chev';
    chev.textContent = '▸';
    kicker.appendChild(chev);

    var saved = null;
    try { saved = localStorage.getItem(key); } catch (e) {}
    var collapsed = saved === null ? panel !== firstLeft : saved === '1';
    if (collapsed) panel.classList.add('is-collapsed');

    kicker.addEventListener('click', function () {
      var now = panel.classList.toggle('is-collapsed');
      try { localStorage.setItem(key, now ? '1' : '0'); } catch (e) {}
    });
  });

  /* Mirrors STATUS_HUE in pulse/tools.py -- one meaning system. Client
     pages pass a priority instead; those map onto the same jewels. */
  var HUES = {
    lead: '#06b6d4', proposal: '#06b6d4',
    negotiation: '#6366f1', confirmed: '#6366f1',
    in_progress: '#0ea5e9', review: '#0ea5e9',
    completed: '#10b981', on_hold: '#ef4444', cancelled: '#94a3b8',
    high: '#ef4444', medium: '#f59e0b', low: '#10b981'
  };
  var hue = HUES[stage.dataset.status] || '#0ea5e9';

  function rgb(hex) {
    var h = hex.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function rgba(hex, a) {
    var c = rgb(hex);
    return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')';
  }
  function mix(hex, other, amt) {
    var a = rgb(hex), b = rgb(other);
    return 'rgb(' + a.map(function (v, i) {
      return Math.round(v + (b[i] - v) * amt);
    }).join(',') + ')';
  }

  /* ── Orb ────────────────────────────────────────────────────────── */

  var orbCtx = orbCanvas.getContext('2d');
  var SIZE = orbCanvas.width;      // square, CSS scales it down
  var R = SIZE * 0.26;

  function drawOrb(t) {
    var cx = SIZE / 2, cy = SIZE / 2;
    orbCtx.clearRect(0, 0, SIZE, SIZE);

    // Light page: a faint tint halo and a soft floor shadow instead of a glow.
    var bloom = orbCtx.createRadialGradient(cx, cy, R * 0.8, cx, cy, R * 1.9);
    bloom.addColorStop(0, rgba(hue, .14));
    bloom.addColorStop(0.5, rgba(hue, .05));
    bloom.addColorStop(1, rgba(hue, 0));
    orbCtx.fillStyle = bloom;
    orbCtx.fillRect(0, 0, SIZE, SIZE);

    var shadow = orbCtx.createRadialGradient(cx, cy + R * 1.02, 0, cx, cy + R * 1.02, R * 0.9);
    shadow.addColorStop(0, 'rgba(15, 23, 42, .16)');
    shadow.addColorStop(1, 'rgba(15, 23, 42, 0)');
    orbCtx.fillStyle = shadow;
    orbCtx.beginPath();
    orbCtx.ellipse(cx, cy + R * 1.02, R * 0.9, R * 0.22, 0, 0, Math.PI * 2);
    orbCtx.fill();

    drawRing(cx, cy, R * 1.24, t, 0.0, rgba(hue, .45), 1.3, 15);
    drawRing(cx, cy, R * 1.40, t, 2.1, 'rgba(148, 163, 184, .35)', 1, 11);

    var body = orbCtx.createRadialGradient(
      cx - R * 0.36, cy - R * 0.40, R * 0.06, cx, cy, R * 1.05
    );
    body.addColorStop(0.00, mix(hue, '#ffffff', .8));
    body.addColorStop(0.30, mix(hue, '#ffffff', .35));
    body.addColorStop(0.65, hue);
    body.addColorStop(1.00, mix(hue, '#0f172a', .3));
    orbCtx.beginPath();
    orbCtx.arc(cx, cy, R, 0, Math.PI * 2);
    orbCtx.fillStyle = body;
    orbCtx.fill();

    var rim = orbCtx.createRadialGradient(
      cx + R * 0.22, cy + R * 0.30, R * 0.5, cx, cy, R
    );
    rim.addColorStop(0, 'rgba(15, 23, 42, 0)');
    rim.addColorStop(1, 'rgba(15, 23, 42, .18)');
    orbCtx.beginPath();
    orbCtx.arc(cx, cy, R, 0, Math.PI * 2);
    orbCtx.fillStyle = rim;
    orbCtx.fill();

    var hx = cx - R * 0.40, hy = cy - R * 0.44;
    var spec = orbCtx.createRadialGradient(hx, hy, 0, hx, hy, R * 0.40);
    spec.addColorStop(0, 'rgba(255,255,255,.72)');
    spec.addColorStop(0.45, 'rgba(255,255,255,.17)');
    spec.addColorStop(1, 'rgba(255,255,255,0)');
    orbCtx.beginPath();
    orbCtx.ellipse(hx, hy, R * 0.36, R * 0.27, -0.6, 0, Math.PI * 2);
    orbCtx.fillStyle = spec;
    orbCtx.fill();
  }

  function drawRing(cx, cy, radius, t, phase, stroke, width, amp) {
    var steps = 280;
    orbCtx.beginPath();
    for (var i = 0; i <= steps; i++) {
      var a = (i / steps) * Math.PI * 2;
      var n = Math.sin(a * 43 + t * 1.7 + phase) * 0.55
            + Math.sin(a * 27 - t * 1.1 + phase) * 0.42
            + Math.sin(a * 13 + t * 0.8) * 0.3
            + Math.sin(a * 5 + t * 0.35) * 0.22;
      var env = 0.62 + 0.38 * Math.sin(a * 3 - t * 0.5 + phase);
      var r = radius + n * amp * env;
      orbCtx[i === 0 ? 'moveTo' : 'lineTo'](
        cx + Math.cos(a) * r, cy + Math.sin(a) * r
      );
    }
    orbCtx.closePath();
    orbCtx.strokeStyle = stroke;
    orbCtx.lineWidth = width;
    orbCtx.lineJoin = 'round';
    orbCtx.stroke();
  }

  /* ── Tendrils ───────────────────────────────────────────────────── */

  var fieldCtx = fieldCanvas ? fieldCanvas.getContext('2d') : null;
  var dpr = Math.min(window.devicePixelRatio || 1, 2);

  function sizeField() {
    if (!fieldCtx) return;
    var r = stage.getBoundingClientRect();
    fieldCanvas.width = Math.round(r.width * dpr);
    fieldCanvas.height = Math.round(r.height * dpr);
    fieldCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function orbAnchor() {
    var r = orbCanvas.getBoundingClientRect();
    var s = stage.getBoundingClientRect();
    return {
      x: r.left - s.left + r.width / 2,
      y: r.top - s.top + r.height / 2,
      radius: r.width * (R / SIZE)
    };
  }

  function drawField(t) {
    if (!fieldCtx) return;
    var s = stage.getBoundingClientRect();
    fieldCtx.clearRect(0, 0, s.width, s.height);
    if (window.innerWidth <= 1400) return;   // stacked/two-col layout: no tendrils

    var orb = orbAnchor();

    panels.forEach(function (panel, i) {
      // Full-width panels sit under the identity block; a tether to them
      // would run straight through the name, actions and ledger.
      if (panel.classList.contains('sp-wide')) return;
      var c = panel.getBoundingClientRect();
      var px = c.left - s.left, py = c.top - s.top;
      // Arrive at the panel edge nearest the orb.
      var end;
      if (px + c.width < orb.x) end = { x: px + c.width + 2, y: py + Math.min(c.height / 2, 130) };
      else if (px > orb.x) end = { x: px - 2, y: py + Math.min(c.height / 2, 130) };
      else end = { x: px + c.width / 2, y: py - 2 };
      var start = {
        x: orb.x + (end.x < orb.x ? -orb.radius * 0.92 : orb.radius * 0.92),
        y: orb.y
      };
      if (end.y > orb.y + 220) start = { x: orb.x, y: orb.y + orb.radius * 0.92 };
      curve(start, end, t, i);
    });
  }

  function curve(a, b, t, seed) {
    var dx = Math.max(90, Math.abs(b.x - a.x) * 0.55) * (b.x < a.x ? -1 : 1);
    var c1 = { x: a.x + dx, y: a.y };
    var c2 = { x: b.x - dx, y: b.y };
    if (Math.abs(b.x - a.x) < 60) {   // vertical run
      c1 = { x: a.x, y: a.y + 90 };
      c2 = { x: b.x, y: b.y - 90 };
    }

    fieldCtx.beginPath();
    fieldCtx.moveTo(a.x, a.y);
    fieldCtx.bezierCurveTo(c1.x, c1.y, c2.x, c2.y, b.x, b.y);
    fieldCtx.strokeStyle = 'rgba(148, 163, 184, .55)';   // slate on white
    fieldCtx.lineWidth = 1.2;
    fieldCtx.stroke();

    var p = ((t * 0.075) + seed * 0.19) % 1;
    var u = 1 - p;
    var pt = {
      x: u*u*u*a.x + 3*u*u*p*c1.x + 3*u*p*p*c2.x + p*p*p*b.x,
      y: u*u*u*a.y + 3*u*u*p*c1.y + 3*u*p*p*c2.y + p*p*p*b.y
    };
    var g = fieldCtx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, 5);
    g.addColorStop(0, rgba(hue, 1));
    g.addColorStop(1, rgba(hue, 0));
    fieldCtx.beginPath();
    fieldCtx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
    fieldCtx.fillStyle = g;
    fieldCtx.fill();
  }

  /* ── Loop ───────────────────────────────────────────────────────── */

  var t0 = null;
  function frame(ts) {
    if (t0 === null) t0 = ts;
    var t = (ts - t0) / 1000;
    drawOrb(t);
    drawField(t);
    requestAnimationFrame(frame);
  }

  window.addEventListener('resize', function () {
    sizeField();
    if (reduce) { drawOrb(0); drawField(0); }
  });

  sizeField();
  if (reduce) { drawOrb(0); drawField(0); }
  else requestAnimationFrame(frame);
})();
