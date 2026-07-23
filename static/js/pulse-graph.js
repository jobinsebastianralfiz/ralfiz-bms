/* ==========================================================================
   PULSE portfolio constellation

   Renders the business as a graph: Ralfiz at the core, clients as jewel-toned
   spheres, their projects as satellite beads on dashed tethers.

   Two camera states, nothing in between. The overview is deliberately quiet —
   spheres and beams only, one label following the pointer — because at real
   data volume (35 clients) permanent labels collide into noise. Clicking a
   client flies the camera to it; that focus state is where names, statuses
   and overdue chips live. Esc, the Overview button, or clicking empty space
   flies back.

   Everything is drawn to one canvas because the reference look depends on
   volumetric beams and shaded spheres that DOM cannot produce cheaply. The
   canvas is aria-hidden and a real list of the same data sits beside it for
   screen readers and keyboard users -- the picture is never the only route
   to the information.

   Geometry draws under the camera transform; text draws in screen space via
   worldToScreen() so type stays the same crisp size at any zoom.
   ========================================================================== */

(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var canvas  = document.getElementById('graph-canvas');
  var stage   = document.getElementById('graph-canvas-wrap');
  var panel   = document.getElementById('graph-panel');
  var backBtn = document.getElementById('graph-overview-btn');
  if (!canvas || !stage) return;

  var ctx = canvas.getContext('2d');
  var dpr = Math.min(window.devicePixelRatio || 1, 2);

  var GOLD = '#e8c07a';
  var ROSE = '#e08aa0';
  var data = JSON.parse(document.getElementById('graph-data').textContent);

  var inr = new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0
  });

  var selected  = null;   // node id driving the right panel
  var hovered   = null;
  var focusedId = null;   // node id the camera is flown to (null = overview)
  var layout    = { core: null, nodes: [] };

  /* Camera. Identity in overview; framing the focused client at FOCUS_SCALE
     otherwise. `cam` eases toward `camTo` every frame. */
  var FOCUS_SCALE = 2.2;
  var cam   = { x: 0, y: 0, scale: 1 };
  var camTo = { x: 0, y: 0, scale: 1 };

  /* fans[id] eases 0→1 as that node's satellites spread into the focus fan.
     Keyed by id, not stored on layout nodes, so a resize relayout cannot
     reset an animation in flight. focusAmt is the global ghosting amount. */
  var fans = {};
  var focusAmt = 0;

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
        var spread = Math.max(node.satellites.length - 1, 1);
        // Overview: tight fan hugging the node. Focus: a wide arc with room
        // for each project's label. Satellites lerp between the two.
        var oa = a + (-0.34 + (j / spread) * 0.68);
        var or_ = size + 34 + (j % 2) * 16;
        var fa = a + (-0.85 + (j / spread) * 1.7);
        var fr = size + 58 + (j % 2) * 24;
        return {
          data: s,
          ox: x + Math.cos(oa) * or_, oy: y + Math.sin(oa) * or_,
          fx: x + Math.cos(fa) * fr,  fy: y + Math.sin(fa) * fr,
          x: 0, y: 0,   // current draw position, set per frame
          r: 5.5
        };
      });

      layout.nodes.push({
        data: node, x: x, y: y, r: size, angle: a, satellites: sats,
        flagged: node.satellites.some(function (s) {
          return s.needs_attention || s.tag != null;
        })
      });
    });
  }

  function overviewCam() {
    return { x: stage.clientWidth / 2, y: stage.clientHeight / 2, scale: 1 };
  }

  function focusCam(n) {
    // Anchor the focused client left of centre, clear of the right panel.
    var w = stage.clientWidth, h = stage.clientHeight;
    return {
      x: n.x - (w * 0.40 - w / 2) / FOCUS_SCALE,
      y: n.y - (h * 0.48 - h / 2) / FOCUS_SCALE,
      scale: FOCUS_SCALE
    };
  }

  function worldToScreen(x, y) {
    return {
      x: (x - cam.x) * cam.scale + stage.clientWidth / 2,
      y: (y - cam.y) * cam.scale + stage.clientHeight / 2
    };
  }

  function screenToWorld(x, y) {
    return {
      x: (x - stage.clientWidth / 2) / cam.scale + cam.x,
      y: (y - stage.clientHeight / 2) / cam.scale + cam.y
    };
  }

  function nodeById(id) {
    return layout.nodes.filter(function (n) { return n.data.id === id; })[0];
  }

  function resize() {
    canvas.width = Math.round(stage.clientWidth * dpr);
    canvas.height = Math.round(stage.clientHeight * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    computeLayout();
    var f = focusedId && nodeById(focusedId);
    camTo = f ? focusCam(f) : overviewCam();
    if (reduce) snap();
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

  function namePlate(label, lx, ly, hue) {
    ctx.font = '600 13px Inter, sans-serif';
    var tw = ctx.measureText(label).width;
    // Plate behind the text keeps it legible over beams and beads.
    ctx.fillStyle = 'rgba(5,9,11,.62)';
    roundRect(lx - 6, ly - 12, tw + 12, 18, 5); ctx.fill();
    ctx.fillStyle = hue;
    ctx.fillText(label, lx, ly);
    return tw;
  }

  function truncate(s) {
    return s.length > 20 ? s.slice(0, 19) + '…' : s;
  }

  /* ── Frame ──────────────────────────────────────────────────────── */

  function ghostAlpha(n) {
    // In focus, everything but the focused client dims to a ghost that is
    // still visible enough to click for the next fly.
    return n.data.id === focusedId ? 1 : 1 - 0.85 * focusAmt;
  }

  function draw(t) {
    var w = stage.clientWidth, h = stage.clientHeight;
    ctx.clearRect(0, 0, w, h);
    var core = layout.core;

    /* World pass — geometry under the camera transform. */
    ctx.save();
    ctx.translate(w / 2, h / 2);
    ctx.scale(cam.scale, cam.scale);
    ctx.translate(-cam.x, -cam.y);

    // Current satellite positions: lerp overview fan → focus fan.
    layout.nodes.forEach(function (n) {
      var fan = fans[n.data.id] || 0;
      n.satellites.forEach(function (s) {
        s.x = s.ox + (s.fx - s.ox) * fan;
        s.y = s.oy + (s.fy - s.oy) * fan;
      });
    });

    // Beams first, so nodes sit on top
    layout.nodes.forEach(function (n) {
      ctx.globalAlpha = ghostAlpha(n);
      var isSel = selected === n.data.id;
      beam(core.x, core.y, n.x, n.y, n.data.hue, isSel ? 1.6 : 1);
    });

    // Satellite tethers
    layout.nodes.forEach(function (n) {
      ctx.globalAlpha = ghostAlpha(n);
      ctx.setLineDash([2, 4]);
      ctx.strokeStyle = hexA(n.data.hue, .3);
      ctx.lineWidth = 1;
      n.satellites.forEach(function (s) {
        ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(s.x, s.y); ctx.stroke();
      });
      ctx.setLineDash([]);
    });

    ctx.globalAlpha = 1 - 0.6 * focusAmt;
    sunCore(core.x, core.y, core.r, reduce ? 0 : t);

    // Spheres first, labels second. Drawing them per-node interleaved let a
    // later node's satellite paint over an earlier node's label.
    layout.nodes.forEach(function (n) {
      ctx.globalAlpha = ghostAlpha(n);
      var bob = reduce ? 0 : Math.sin(t * 0.7 + n.angle * 3) * 2.2;
      n.bob = bob;
      n.satellites.forEach(function (s) {
        sphere(s.x, s.y + bob * 0.6, s.r, s.data.hue, false);
      });
      sphere(n.x, n.y + bob, n.r, n.data.hue, selected === n.data.id);

      // Risk is the one thing the quiet overview must not hide: a rose
      // ember pinned to any client with an overdue or flagged project.
      if (n.flagged) {
        var mx = n.x + n.r * 0.78, my = n.y + bob - n.r * 0.78;
        var halo = ctx.createRadialGradient(mx, my, 0, mx, my, 9);
        halo.addColorStop(0, hexA(ROSE, .55));
        halo.addColorStop(1, hexA(ROSE, 0));
        ctx.fillStyle = halo;
        ctx.beginPath(); ctx.arc(mx, my, 9, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = ROSE;
        ctx.beginPath(); ctx.arc(mx, my, 3, 0, Math.PI * 2); ctx.fill();
      }
    });

    ctx.restore();
    ctx.globalAlpha = 1;

    /* Screen pass — text at constant size regardless of zoom. */

    // Core label
    ctx.globalAlpha = 1 - 0.6 * focusAmt;
    var cs = worldToScreen(core.x, core.y);
    ctx.font = '700 17px Inter, sans-serif';
    ctx.fillStyle = '#e9f2f4';
    ctx.fillText(data.core.label, cs.x + core.r * cam.scale + 16, cs.y + 2);
    ctx.font = '500 11px Inter, sans-serif';
    ctx.fillStyle = '#7c94a0';
    ctx.fillText(
      data.core.client_count + ' clients · ' + data.core.project_count + ' projects',
      cs.x + core.r * cam.scale + 16, cs.y + 18
    );
    ctx.globalAlpha = 1;

    // One label in the overview: the node under the pointer. The focused
    // node keeps a permanent label; everything else stays quiet.
    layout.nodes.forEach(function (n) {
      var isFoc = focusedId === n.data.id;
      var fan = fans[n.data.id] || 0;
      if (!isFoc && hovered !== n.data.id) return;

      var p = worldToScreen(n.x, n.y + (n.bob || 0));
      // Labels sit on whichever side has more room, so they stop colliding
      // with the satellites fanned out around the node.
      var right = n.x < stage.clientWidth * 0.56;
      var label = truncate(n.data.label);
      ctx.font = '600 13px Inter, sans-serif';
      var tw = ctx.measureText(label).width;
      var lx = right ? p.x + n.r * cam.scale + 13 : p.x - n.r * cam.scale - 13 - tw;
      var ly = p.y + 1;

      namePlate(label, lx, ly, isFoc && selected === n.data.id ? GOLD : '#e9f2f4');
      chip(n.data.share + '%', lx, ly + 17,
        isFoc && selected === n.data.id ? GOLD : n.data.hue);

      // Project detail belongs to the focus state; fade it in with the fan.
      if (isFoc && fan > 0.05) {
        ctx.globalAlpha = fan;
        n.satellites.forEach(function (s) {
          var sp = worldToScreen(s.x, s.y + (n.bob || 0) * 0.6);
          var sx = sp.x + s.r * cam.scale + 8;
          namePlate(truncate(s.data.label), sx, sp.y - 6, '#e9f2f4');
          var cw = chip(s.data.status_display, sx, sp.y + 11, s.data.hue);
          if (s.data.tag != null) {
            chip(s.data.tag + 'd late', sx + cw + 5, sp.y + 11, ROSE);
          }
        });
        ctx.globalAlpha = 1;
      }
    });
  }

  /* ── Animation ──────────────────────────────────────────────────── */

  function step(dt) {
    // Exponential approach: retargeting mid-flight (client A → client B)
    // stays smooth because the camera only ever chases camTo.
    var k = 1 - Math.pow(0.002, dt / 0.55);
    cam.x += (camTo.x - cam.x) * k;
    cam.y += (camTo.y - cam.y) * k;
    cam.scale += (camTo.scale - cam.scale) * k;
    focusAmt += ((focusedId ? 1 : 0) - focusAmt) * k;
    layout.nodes.forEach(function (n) {
      var id = n.data.id;
      var cur = fans[id] || 0;
      fans[id] = cur + ((focusedId === id ? 1 : 0) - cur) * k;
    });
  }

  function snap() {
    cam.x = camTo.x; cam.y = camTo.y; cam.scale = camTo.scale;
    focusAmt = focusedId ? 1 : 0;
    layout.nodes.forEach(function (n) {
      fans[n.data.id] = focusedId === n.data.id ? 1 : 0;
    });
    draw(0);
  }

  var t0 = null, last = null;
  function frame(ts) {
    if (t0 === null) t0 = ts;
    var dt = last === null ? 16 : Math.min(ts - last, 50);
    last = ts;
    step(dt / 1000);
    draw((ts - t0) / 1000);
    requestAnimationFrame(frame);
  }

  /* ── Interaction ────────────────────────────────────────────────── */

  function hit(mx, my) {
    var p = screenToWorld(mx, my);
    for (var i = 0; i < layout.nodes.length; i++) {
      var n = layout.nodes[i];
      // A focused client's fanned-out satellites are click targets that lead
      // to the project page. Only once fanned: in the overview the beads
      // huddle against their client and a miss would swallow the client click.
      if ((fans[n.data.id] || 0) > 0.5) {
        for (var j = 0; j < n.satellites.length; j++) {
          var s = n.satellites[j];
          if (Math.hypot(p.x - s.x, p.y - s.y) < s.r + 8) {
            return { node: n, sat: s };
          }
        }
      }
      if (Math.hypot(p.x - n.x, p.y - n.y) < n.r + 10) return { node: n, sat: null };
    }
    return null;
  }

  canvas.addEventListener('mousemove', function (e) {
    var r = canvas.getBoundingClientRect();
    var h = hit(e.clientX - r.left, e.clientY - r.top);
    var id = h ? (h.sat ? h.sat.data.id : h.node.data.id) : null;
    canvas.style.cursor = h ? 'pointer' : 'default';
    if (id !== hovered) {
      hovered = id;
      // No animation loop under reduced motion, so hover must repaint itself.
      if (reduce) draw(0);
    }
  });

  canvas.addEventListener('click', function (e) {
    var r = canvas.getBoundingClientRect();
    var h = hit(e.clientX - r.left, e.clientY - r.top);
    if (h && h.sat) {
      // Satellite ids are 'project:<uuid>'; the detail page lives in core.
      window.location.href = '/projects/' + h.sat.data.id.slice(8) + '/';
    } else if (h) {
      select(h.node.data.id);
      flyTo(h.node.data.id);
    } else if (focusedId) {
      toOverview();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && focusedId) toOverview();
  });

  if (backBtn) backBtn.addEventListener('click', toOverview);

  function flyTo(id) {
    var n = nodeById(id);
    if (!n) return;
    focusedId = id;
    camTo = focusCam(n);
    if (backBtn) backBtn.hidden = false;
    if (reduce) snap();
  }

  function toOverview() {
    focusedId = null;
    camTo = overviewCam();
    if (backBtn) backBtn.hidden = true;
    if (reduce) snap();
  }

  /* Selection drives the right panel; the camera is handled separately so
     boot can select a client without flying at the viewer. */
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
            return '<li><a class="graph-panel__link" href="/projects/' +
              esc(s.id.slice(8)) + '/">' +
              '<span class="dot" style="background:' + s.hue + '"></span>' +
              '<span class="nm">' + esc(s.label) + '</span>' +
              '<span class="st">' + esc(s.status_display) + '</span>' +
              (s.tag != null ? '<span class="ov">' + s.tag + 'd late</span>' : '') +
              '</a></li>';
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

  /* ── Reacting to answers ────────────────────────────────────────── */

  // The command bar (pulse-ask.js) calls this with {answer, intent, data}
  // after every successful ask. Point the constellation at whatever the
  // answer is about: match project UUIDs from the structured payload and
  // client names from the text against the graph, and fly there.
  //
  // Only when exactly ONE client is implicated. A business-wide answer
  // (overdue invoices across four clients) names many; flying to the first
  // would be arbitrary and read as PULSE misunderstanding the question.
  window.pulseOnAnswer = function (body) {
    if (!body) return;
    var hits = {};
    var blob = JSON.stringify(body.data || '');
    var text = ((body.answer || '') + ' ' + blob).toLowerCase();

    // Project ids in the payload → the client that owns that satellite.
    var uuidRe = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
    var m;
    while ((m = uuidRe.exec(blob))) {
      var uid = m[0].toLowerCase();
      data.nodes.forEach(function (n) {
        if (n.id === 'client:' + uid) hits[n.id] = true;
        else if (n.satellites.some(function (s) { return s.id === 'project:' + uid; })) {
          hits[n.id] = true;
        }
      });
    }

    // Client names in the prose. Short labels are skipped: a two-letter
    // name would substring-match half the dictionary.
    data.nodes.forEach(function (n) {
      if (n.label && n.label.length >= 4 &&
          text.indexOf(n.label.toLowerCase()) !== -1) {
        hits[n.id] = true;
      }
    });

    var ids = Object.keys(hits);
    if (ids.length === 1) {
      select(ids[0]);
      flyTo(ids[0]);
    }
  };

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
  // The stage also resizes WITHOUT a window resize — the weather card
  // arriving async reflows the grid. A stale bitmap leaves a bottom band
  // that clearRect() no longer covers, and every frame smears into it.
  if (window.ResizeObserver) {
    new ResizeObserver(function () {
      if (canvas.width !== Math.round(stage.clientWidth * dpr) ||
          canvas.height !== Math.round(stage.clientHeight * dpr)) {
        resize();
      }
    }).observe(stage);
  }
  cam = overviewCam();
  camTo = overviewCam();
  resize();

  document.querySelectorAll('.graph-list__item').forEach(function (el) {
    el.addEventListener('click', function () {
      select(el.dataset.node);
      flyTo(el.dataset.node);
    });
    el.addEventListener('focus', function () { hovered = el.dataset.node; });
    el.addEventListener('blur', function () { hovered = null; });
  });

  if (data.nodes.length) select(data.nodes[0].id);
  if (reduce) draw(0); else requestAnimationFrame(frame);
})();
