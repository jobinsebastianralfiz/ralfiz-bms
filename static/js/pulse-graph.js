/* ==========================================================================
   PULSE portfolio constellation

   Renders the business as a graph: Ralfiz at the core, clients as jewel-toned
   spheres, their projects as satellite beads on dashed tethers.

   Everything is drawn to one canvas because the reference look depends on
   volumetric beams and shaded spheres that DOM cannot produce cheaply. The
   canvas is aria-hidden and a real list of the same data sits beside it for
   screen readers and keyboard users -- the picture is never the only route
   to the information.
   ========================================================================== */

(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var canvas = document.getElementById('graph-canvas');
  var stage  = document.getElementById('graph-canvas-wrap');
  var panel  = document.getElementById('graph-panel');
  if (!canvas || !stage) return;

  var ctx = canvas.getContext('2d');
  var dpr = Math.min(window.devicePixelRatio || 1, 2);

  var GOLD = '#e8c07a';
  var data = JSON.parse(document.getElementById('graph-data').textContent);

  var inr = new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0
  });

  var selected = null;   // node id
  var hovered  = null;
  var layout   = { core: null, nodes: [] };

  /* ── Layout ─────────────────────────────────────────────────────── */

  function computeLayout() {
    var w = stage.clientWidth, h = stage.clientHeight;
    var cx = w * 0.40, cy = h * 0.50;
    var ring = Math.min(w, h) * 0.34;

    layout.core = { x: cx, y: cy, r: Math.min(w, h) * 0.055 };
    layout.nodes = [];

    var n = data.nodes.length || 1;
    data.nodes.forEach(function (node, i) {
      // Spread around the core, biased away from the panel on the right.
      var a = (-Math.PI * 0.62) + (i / n) * (Math.PI * 1.72);
      // Vary radius by billing share so the picture is not a plain circle.
      var jitter = 1 + ((i % 3) - 1) * 0.13;
      var r = ring * jitter;
      var x = cx + Math.cos(a) * r * 1.28;
      var y = cy + Math.sin(a) * r;

      // Node size carries project count, floored so empty clients stay visible.
      var size = 13 + Math.min(node.project_count, 6) * 3.2;

      var sats = node.satellites.map(function (s, j) {
        var sa = a + (-0.34 + (j / Math.max(node.satellites.length - 1, 1)) * 0.68);
        var sr = size + 34 + (j % 2) * 16;
        return {
          data: s,
          x: x + Math.cos(sa) * sr,
          y: y + Math.sin(sa) * sr,
          r: 5.5
        };
      });

      layout.nodes.push({ data: node, x: x, y: y, r: size, angle: a, satellites: sats });
    });
  }

  function resize() {
    canvas.width = Math.round(stage.clientWidth * dpr);
    canvas.height = Math.round(stage.clientHeight * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    computeLayout();
  }

  /* ── Drawing primitives ─────────────────────────────────────────── */

  function sphere(x, y, r, hue, lit) {
    // Bloom
    var bloom = ctx.createRadialGradient(x, y, r * 0.7, x, y, r * 2.6);
    bloom.addColorStop(0, hexA(hue, lit ? .34 : .2));
    bloom.addColorStop(1, hexA(hue, 0));
    ctx.fillStyle = bloom;
    ctx.beginPath(); ctx.arc(x, y, r * 2.6, 0, Math.PI * 2); ctx.fill();

    // Body, lit from upper-left
    var g = ctx.createRadialGradient(
      x - r * 0.36, y - r * 0.4, r * 0.05, x, y, r * 1.05
    );
    g.addColorStop(0, mix(hue, '#ffffff', .68));
    g.addColorStop(0.34, mix(hue, '#ffffff', .2));
    g.addColorStop(0.72, hue);
    g.addColorStop(1, mix(hue, '#000000', .58));
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = g; ctx.fill();

    // Rim shadow
    var rim = ctx.createRadialGradient(
      x + r * 0.24, y + r * 0.3, r * 0.42, x, y, r
    );
    rim.addColorStop(0, 'rgba(4,10,12,0)');
    rim.addColorStop(1, 'rgba(4,10,12,.5)');
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = rim; ctx.fill();

    // Specular
    var hx = x - r * 0.38, hy = y - r * 0.42;
    var s = ctx.createRadialGradient(hx, hy, 0, hx, hy, r * 0.42);
    s.addColorStop(0, 'rgba(255,255,255,.75)');
    s.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.beginPath();
    ctx.ellipse(hx, hy, r * 0.34, r * 0.25, -0.6, 0, Math.PI * 2);
    ctx.fillStyle = s; ctx.fill();

    if (lit) {
      ctx.beginPath(); ctx.arc(x, y, r + 4, 0, Math.PI * 2);
      ctx.strokeStyle = hexA(GOLD, .75); ctx.lineWidth = 1.5; ctx.stroke();
    }
  }

  function sunCore(x, y, r, t) {
    // Volumetric halo
    var halo = ctx.createRadialGradient(x, y, r * 0.5, x, y, r * 4.2);
    halo.addColorStop(0, 'rgba(232,192,122,.3)');
    halo.addColorStop(0.4, 'rgba(200,150,80,.09)');
    halo.addColorStop(1, 'rgba(200,150,80,0)');
    ctx.fillStyle = halo;
    ctx.beginPath(); ctx.arc(x, y, r * 4.2, 0, Math.PI * 2); ctx.fill();

    // Concentric ornate rings, counter-rotating
    for (var k = 0; k < 3; k++) {
      var rr = r * (1.3 + k * 0.34);
      var dir = k % 2 ? -1 : 1;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(t * 0.06 * dir + k);
      ctx.beginPath();
      var teeth = 34 + k * 12;
      for (var i = 0; i <= teeth; i++) {
        var a = (i / teeth) * Math.PI * 2;
        var spike = (i % 2 ? 1 : 0.9) * rr;
        var px = Math.cos(a) * spike, py = Math.sin(a) * spike;
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.strokeStyle = 'rgba(232,192,122,' + (0.4 - k * 0.1) + ')';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.restore();
    }

    sphere(x, y, r, '#d8a860', false);
  }

  function beam(x1, y1, x2, y2, hue, strength) {
    // Volumetric: a wide soft pass for the glow, a narrow bright pass for the
    // core of the streak. A single hairline reads as a wireframe, not light.
    var wide = ctx.createLinearGradient(x1, y1, x2, y2);
    wide.addColorStop(0, hexA(GOLD, .3 * strength));
    wide.addColorStop(0.45, hexA(hue, .16 * strength));
    wide.addColorStop(1, hexA(hue, 0));
    ctx.strokeStyle = wide;
    ctx.lineWidth = 11 * strength;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();

    var core = ctx.createLinearGradient(x1, y1, x2, y2);
    core.addColorStop(0, hexA(GOLD, .75 * strength));
    core.addColorStop(0.5, hexA(hue, .42 * strength));
    core.addColorStop(1, hexA(hue, .05));
    ctx.strokeStyle = core;
    ctx.lineWidth = 1.8 * strength;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.lineCap = 'butt';
  }

  function chip(text, x, y, hue) {
    ctx.font = '600 10px Inter, sans-serif';
    var w = ctx.measureText(text).width + 12;
    ctx.fillStyle = 'rgba(6,18,21,.82)';
    roundRect(x, y - 8, w, 16, 8); ctx.fill();
    ctx.strokeStyle = hexA(hue, .35); ctx.lineWidth = 1;
    roundRect(x, y - 8, w, 16, 8); ctx.stroke();
    ctx.fillStyle = hue;
    ctx.fillText(text, x + 6, y + 3.5);
    return w;
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  /* ── Frame ──────────────────────────────────────────────────────── */

  function draw(t) {
    var w = stage.clientWidth, h = stage.clientHeight;
    ctx.clearRect(0, 0, w, h);
    var core = layout.core;

    // Beams first, so nodes sit on top
    layout.nodes.forEach(function (n) {
      var isSel = selected === n.data.id;
      beam(core.x, core.y, n.x, n.y, n.data.hue, isSel ? 1.6 : 1);
    });

    // Satellite tethers
    layout.nodes.forEach(function (n) {
      ctx.setLineDash([2, 4]);
      ctx.strokeStyle = hexA(n.data.hue, .3);
      ctx.lineWidth = 1;
      n.satellites.forEach(function (s) {
        ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(s.x, s.y); ctx.stroke();
      });
      ctx.setLineDash([]);
    });

    sunCore(core.x, core.y, core.r, reduce ? 0 : t);

    // Core label
    ctx.font = '700 17px Inter, sans-serif';
    ctx.fillStyle = '#e9f2f4';
    ctx.fillText(data.core.label, core.x + core.r + 16, core.y + 2);
    ctx.font = '500 11px Inter, sans-serif';
    ctx.fillStyle = '#7c94a0';
    ctx.fillText(
      data.core.client_count + ' clients · ' + data.core.project_count + ' projects',
      core.x + core.r + 16, core.y + 18
    );

    // Spheres first, labels second. Drawing them per-node interleaved let a
    // later node's satellite paint over an earlier node's label.
    layout.nodes.forEach(function (n) {
      var bob = reduce ? 0 : Math.sin(t * 0.7 + n.angle * 3) * 2.2;
      n.bob = bob;
      n.satellites.forEach(function (s) {
        sphere(s.x, s.y + bob * 0.6, s.r, s.data.hue, false);
      });
      sphere(n.x, n.y + bob, n.r, n.data.hue, selected === n.data.id);
    });

    layout.nodes.forEach(function (n) {
      var isSel = selected === n.data.id;
      var isHov = hovered === n.data.id;

      n.satellites.forEach(function (s) {
        if (s.data.tag != null) {
          chip(s.data.tag + 'd', s.x + 9, s.y + n.bob * 0.6 - 9, '#e08aa0');
        }
      });

      // Labels sit on whichever side has more room, so they stop colliding
      // with the satellites fanned out around the node.
      var right = n.x < stage.clientWidth * 0.56;
      ctx.font = (isSel || isHov ? '700 ' : '600 ') + '13px Inter, sans-serif';
      var label = n.data.label.length > 20
        ? n.data.label.slice(0, 19) + '…' : n.data.label;
      var tw = ctx.measureText(label).width;
      var lx = right ? n.x + n.r + 13 : n.x - n.r - 13 - tw;
      var ly = n.y + n.bob + 1;

      // Plate behind the text keeps it legible over beams and beads.
      ctx.fillStyle = 'rgba(5,9,11,.62)';
      roundRect(lx - 6, ly - 12, tw + 12, 18, 5); ctx.fill();

      ctx.fillStyle = isSel ? GOLD : '#e9f2f4';
      ctx.fillText(label, lx, ly);
      chip(n.data.share + '%', lx, ly + 17, isSel ? GOLD : n.data.hue);
    });
  }

  var t0 = null;
  function frame(ts) {
    if (t0 === null) t0 = ts;
    draw((ts - t0) / 1000);
    requestAnimationFrame(frame);
  }

  /* ── Interaction ────────────────────────────────────────────────── */

  function hit(mx, my) {
    for (var i = 0; i < layout.nodes.length; i++) {
      var n = layout.nodes[i];
      if (Math.hypot(mx - n.x, my - n.y) < n.r + 10) return n;
    }
    return null;
  }

  canvas.addEventListener('mousemove', function (e) {
    var r = canvas.getBoundingClientRect();
    var n = hit(e.clientX - r.left, e.clientY - r.top);
    hovered = n ? n.data.id : null;
    canvas.style.cursor = n ? 'pointer' : 'default';
  });

  canvas.addEventListener('click', function (e) {
    var r = canvas.getBoundingClientRect();
    var n = hit(e.clientX - r.left, e.clientY - r.top);
    if (n) select(n.data.id);
  });

  function select(id) {
    selected = id;
    var node = data.nodes.filter(function (n) { return n.id === id; })[0];
    if (!node) return;
    renderPanel(node);
    document.querySelectorAll('.graph-list__item').forEach(function (el) {
      el.classList.toggle('is-selected', el.dataset.node === id);
    });
  }

  function renderPanel(node) {
    var attention = node.satellites.filter(function (s) { return s.needs_attention; });
    panel.innerHTML =
      '<p class="graph-panel__kicker">Client</p>' +
      '<h2 class="graph-panel__title">' + esc(node.label) + '</h2>' +
      (node.company ? '<p class="graph-panel__sub">' + esc(node.company) + '</p>' : '') +
      '<div class="graph-panel__stats">' +
        stat(node.project_count, 'Projects') +
        stat(node.active_count, 'Active') +
        stat(inr.format(node.billed), 'Billed') +
        // Billed is not owed. Showing only the former reads as debt.
        stat(inr.format(node.outstanding), 'Still owed') +
      '</div>' +
      (attention.length
        ? '<p class="graph-panel__flag">' + attention.length +
          (attention.length === 1 ? ' project needs' : ' projects need') + ' a human</p>'
        : '') +
      '<h3 class="graph-panel__h3">Projects</h3>' +
      (node.satellites.length
        ? '<ul class="graph-panel__list">' + node.satellites.map(function (s) {
            return '<li><span class="dot" style="background:' + s.hue + '"></span>' +
              '<span class="nm">' + esc(s.label) + '</span>' +
              '<span class="st">' + esc(s.status_display) + '</span>' +
              (s.tag != null ? '<span class="ov">' + s.tag + 'd late</span>' : '') +
              '</li>';
          }).join('') + '</ul>'
        : '<p class="graph-panel__empty">No projects yet. This client is a relationship, not a pipeline.</p>');
  }

  function stat(v, l) {
    return '<div class="graph-stat"><span class="graph-stat__v">' + v +
           '</span><span class="graph-stat__l">' + l + '</span></div>';
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* ── Colour helpers ─────────────────────────────────────────────── */

  function rgb(hex) {
    var h = hex.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function hexA(hex, a) {
    var c = rgb(hex);
    return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')';
  }
  function mix(hex, other, amt) {
    var a = rgb(hex), b = rgb(other);
    return 'rgb(' + a.map(function (v, i) {
      return Math.round(v + (b[i] - v) * amt);
    }).join(',') + ')';
  }

  /* ── Boot ───────────────────────────────────────────────────────── */

  window.addEventListener('resize', resize);
  resize();

  document.querySelectorAll('.graph-list__item').forEach(function (el) {
    el.addEventListener('click', function () { select(el.dataset.node); });
    el.addEventListener('focus', function () { hovered = el.dataset.node; });
    el.addEventListener('blur', function () { hovered = null; });
  });

  if (data.nodes.length) select(data.nodes[0].id);
  if (reduce) draw(0); else requestAnimationFrame(frame);
})();
