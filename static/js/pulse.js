/* ==========================================================================
   PULSE Command Center
   Self-contained. Does not touch the project's global app.js.

   Two canvases:
     #pulse-orb   — the signature object: a shaded sphere with a reactive ring
     #pulse-field — bezier tendrils from the orb to each card, with light dots
   Cards stay in the DOM so they keep real focus, hover and screen-reader
   semantics; the field canvas reads their positions each frame.
   ========================================================================== */

(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var orbCanvas   = document.getElementById('pulse-orb');
  var fieldCanvas = document.getElementById('pulse-field');
  var stage       = document.getElementById('pulse-stage');
  var cardsWrap   = document.getElementById('pulse-cards');
  var form        = document.getElementById('pulse-form');
  var input       = document.getElementById('pulse-input');
  var execBtn     = document.getElementById('pulse-execute');
  var micBtn      = document.getElementById('pulse-mic');
  var hint        = document.getElementById('pulse-hint');
  var panel       = document.getElementById('pulse-response');
  var panelBody   = document.getElementById('pulse-response-body');
  var panelIntent = document.getElementById('pulse-response-intent');
  var panelClose  = document.getElementById('pulse-response-close');
  var projectSel  = document.getElementById('pulse-project');

  var cards = Array.prototype.slice.call(document.querySelectorAll('.pulse-card'));

  /* ── Formatting ─────────────────────────────────────────────────── */

  var inr = new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0
  });

  function money(v) { return inr.format(Number(v) || 0); }

  function setField(name, value) {
    var nodes = document.querySelectorAll('[data-field="' + name + '"]');
    for (var i = 0; i < nodes.length; i++) nodes[i].textContent = value;
  }

  /* ── Bind server data to the screen ─────────────────────────────── */

  function render(summary) {
    if (!summary || !summary.found) {
      setField('name', 'No project selected');
      setField('client', '');
      return;
    }

    // Trailing digits in a project name take the gold accent.
    var titleSlot = document.querySelector('[data-field="name"]');
    var m = /^(.*?)(\d[\d/–-]*)$/.exec(summary.name || '');
    if (m) {
      titleSlot.innerHTML = '';
      titleSlot.appendChild(document.createTextNode(m[1]));
      var num = document.createElement('span');
      num.className = 'pulse-num';
      num.textContent = m[2];
      titleSlot.appendChild(num);
    } else {
      titleSlot.textContent = summary.name || '—';
    }

    setField('client', summary.client || '');

    var tasks  = summary.tasks  || { total: 0, open: 0, by_status: {} };
    var issues = summary.issues || { open: 0, critical: 0 };
    var team   = summary.team   || [];

    setField('tasks-open', tasks.open || 0);
    setField('tasks-total', (tasks.total || 0) + ' total');

    setField('team-count', team.length);
    setField('team-names', team.slice(0, 3).map(function (t) { return t.name; }).join(', '));

    setField('issues-open', issues.open || 0);
    setField('issues-open-card', issues.open || 0);
    setField('issues-critical',
      issues.critical ? issues.critical + ' high or critical' : 'none critical');

    setField('billed', money(summary.amount_billed));
    setField('collected', money(summary.amount_collected) + ' collected');

    var done = (tasks.by_status && tasks.by_status.completed) || 0;
    var pct = tasks.total ? Math.round((done / tasks.total) * 100) : 0;
    setField('progress-value', tasks.total ? pct + '%' : 'no tasks');
    var fill = document.querySelector('[data-field="progress-fill"]');
    if (fill) fill.style.width = pct + '%';

    // Gold marks one thing at a time: whichever card most needs a human.
    var priority = issues.open > 0 ? 'blockers' : 'tasks';
    selectCard(priority);
  }

  function selectCard(key) {
    cards.forEach(function (c) {
      c.classList.toggle('is-selected', c.dataset.card === key);
    });
  }

  /* ── The orb ────────────────────────────────────────────────────── */

  var orbCtx = orbCanvas ? orbCanvas.getContext('2d') : null;
  var SIZE = 440, R = 96;

  function drawOrb(t) {
    if (!orbCtx) return;
    var cx = SIZE / 2, cy = SIZE / 2;
    orbCtx.clearRect(0, 0, SIZE, SIZE);

    // Outer bloom
    var bloom = orbCtx.createRadialGradient(cx, cy, R * 0.75, cx, cy, R * 2.1);
    bloom.addColorStop(0, 'rgba(138, 95, 214, .34)');
    bloom.addColorStop(0.45, 'rgba(122, 80, 200, .12)');
    bloom.addColorStop(1, 'rgba(122, 80, 200, 0)');
    orbCtx.fillStyle = bloom;
    orbCtx.fillRect(0, 0, SIZE, SIZE);

    // Reactive ring — a waveform bent into a circle. Two passes for depth.
    drawRing(cx, cy, R * 1.24, t, 0.0, 'rgba(47, 212, 212, .5)', 1.4, 17);
    drawRing(cx, cy, R * 1.40, t, 2.1, 'rgba(167, 139, 214, .32)', 1.1, 13);

    // Sphere body: light comes from upper-left.
    var body = orbCtx.createRadialGradient(
      cx - R * 0.36, cy - R * 0.40, R * 0.06,
      cx, cy, R * 1.05
    );
    body.addColorStop(0.00, '#e6d4ff');
    body.addColorStop(0.28, '#b89af0');
    body.addColorStop(0.62, '#8a5fd6');
    body.addColorStop(1.00, '#4a2a86');
    orbCtx.beginPath();
    orbCtx.arc(cx, cy, R, 0, Math.PI * 2);
    orbCtx.fillStyle = body;
    orbCtx.fill();

    // Rim shadow along the lower edge, so it reads as lit from above-left.
    var rim = orbCtx.createRadialGradient(
      cx + R * 0.22, cy + R * 0.30, R * 0.42,
      cx, cy, R
    );
    rim.addColorStop(0, 'rgba(24, 10, 46, 0)');
    rim.addColorStop(1, 'rgba(24, 10, 46, .55)');
    orbCtx.beginPath();
    orbCtx.arc(cx, cy, R, 0, Math.PI * 2);
    orbCtx.fillStyle = rim;
    orbCtx.fill();

    // Specular highlight, upper-left quadrant.
    var hx = cx - R * 0.40, hy = cy - R * 0.44;
    var spec = orbCtx.createRadialGradient(hx, hy, 0, hx, hy, R * 0.40);
    spec.addColorStop(0, 'rgba(255, 255, 255, .72)');
    spec.addColorStop(0.45, 'rgba(255, 255, 255, .17)');
    spec.addColorStop(1, 'rgba(255, 255, 255, 0)');
    orbCtx.beginPath();
    orbCtx.ellipse(hx, hy, R * 0.36, R * 0.27, -0.6, 0, Math.PI * 2);
    orbCtx.fillStyle = spec;
    orbCtx.fill();
  }

  function drawRing(cx, cy, radius, t, phase, stroke, width, amp) {
    // Enough steps that the high harmonics land as spikes rather than
    // aliasing into a smooth curve.
    var steps = 320;
    orbCtx.beginPath();
    for (var i = 0; i <= steps; i++) {
      var a = (i / steps) * Math.PI * 2;
      // Layered sine noise, weighted toward the high harmonics so the path
      // reads as a waveform bent into a circle -- spiky, not blobby.
      var n = Math.sin(a * 43 + t * 1.7 + phase) * 0.55
            + Math.sin(a * 27 - t * 1.1 + phase) * 0.42
            + Math.sin(a * 13 + t * 0.8) * 0.3
            + Math.sin(a * 5 + t * 0.35) * 0.22;
      // Slow envelope so the spikes swell and settle rather than buzzing flat.
      var env = 0.62 + 0.38 * Math.sin(a * 3 - t * 0.5 + phase);
      var r = radius + n * amp * env;
      var x = cx + Math.cos(a) * r;
      var y = cy + Math.sin(a) * r;
      if (i === 0) orbCtx.moveTo(x, y); else orbCtx.lineTo(x, y);
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
    if (!fieldCanvas || !stage) return;
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
    if (!fieldCtx || !stage) return;
    var s = stage.getBoundingClientRect();
    fieldCtx.clearRect(0, 0, s.width, s.height);
    if (window.innerWidth <= 1080) return;

    var orb = orbAnchor();
    var start = { x: orb.x + orb.radius * 0.92, y: orb.y };

    cards.forEach(function (card, i) {
      var c = card.getBoundingClientRect();
      var end = { x: c.left - s.left - 3, y: c.top - s.top + c.height / 2 };
      var gold = card.classList.contains('is-selected');
      curve(start, end, gold, t, i);
    });

    // One loose tendril curving off-frame — implies graph beyond the view.
    curve(start,
      { x: s.width * 0.52, y: s.height + 70 },
      false, t, 99);
  }

  function curve(a, b, gold, t, seed) {
    // Control points pull horizontally: leaves the orb flat, arrives flat.
    var dx = Math.max(90, (b.x - a.x) * 0.55);
    var c1 = { x: a.x + dx, y: a.y };
    var c2 = { x: b.x - dx, y: b.y };

    fieldCtx.beginPath();
    fieldCtx.moveTo(a.x, a.y);
    fieldCtx.bezierCurveTo(c1.x, c1.y, c2.x, c2.y, b.x, b.y);
    fieldCtx.strokeStyle = gold ? 'rgba(232, 192, 122, .55)' : 'rgba(47, 212, 212, .28)';
    fieldCtx.lineWidth = gold ? 1.6 : 1;
    fieldCtx.stroke();

    // Travelling light dot. Slow, staggered per line.
    var p = ((t * 0.075) + seed * 0.19) % 1;
    var pt = bezierAt(a, c1, c2, b, p);
    var g = fieldCtx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, 5.5);
    var tint = gold ? '232, 192, 122' : '47, 212, 212';
    g.addColorStop(0, 'rgba(' + tint + ', .95)');
    g.addColorStop(1, 'rgba(' + tint + ', 0)');
    fieldCtx.beginPath();
    fieldCtx.arc(pt.x, pt.y, 5.5, 0, Math.PI * 2);
    fieldCtx.fillStyle = g;
    fieldCtx.fill();
  }

  function bezierAt(p0, p1, p2, p3, t) {
    var u = 1 - t;
    return {
      x: u*u*u*p0.x + 3*u*u*t*p1.x + 3*u*t*t*p2.x + t*t*t*p3.x,
      y: u*u*u*p0.y + 3*u*u*t*p1.y + 3*u*t*t*p2.y + t*t*t*p3.y
    };
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

  /* ── Asking ─────────────────────────────────────────────────────── */

  function csrf() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function showAnswer(text, intent, isError) {
    panelIntent.textContent = isError
      ? 'Could not answer'
      : (intent ? intent.replace(/_/g, ' ') : 'Answer');
    panelBody.textContent = text;
    panel.classList.toggle('is-error', !!isError);
    panel.hidden = false;
    requestAnimationFrame(function () { panel.classList.add('is-open'); });
  }

  function flare(intent) {
    var map = {
      get_project_summary: 'tasks',
      get_team_for_project: 'team',
      get_overdue_invoices: 'billing',
      get_outstanding_receivables: 'billing'
    };
    var key = map[intent];
    if (!key) return;
    selectCard(key);
    if (reduceMotion) return;
    var card = cards.filter(function (c) { return c.dataset.card === key; })[0];
    if (!card) return;
    card.classList.remove('is-flaring');
    void card.offsetWidth;
    card.classList.add('is-flaring');
  }

  function ask(query) {
    execBtn.disabled = true;
    hint.classList.remove('is-warning');
    hint.textContent = 'Working through live records…';

    fetch('/api/pulse/ask/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      credentials: 'same-origin',
      body: JSON.stringify({ query: query })
    })
      .then(function (res) {
        return res.json()
          .catch(function () { return {}; })
          .then(function (body) { return { status: res.status, body: body }; });
      })
      .then(function (r) {
        if (r.status === 200) {
          showAnswer(r.body.answer || 'No answer came back.', r.body.intent, false);
          flare(r.body.intent);
          hint.textContent = 'Answers come from live records.';
          return;
        }
        var msg = {
          400: 'That question could not be turned into a query. Try naming the project or date differently.',
          403: 'Your account cannot read business-wide data. PULSE is limited to owner and partner accounts.',
          503: 'PULSE is not configured yet — ANTHROPIC_API_KEY is missing on the server.'
        }[r.status] || (r.body.detail || 'Something went wrong reaching PULSE.');
        showAnswer(msg, null, true);
        hint.textContent = 'Answers come from live records.';
      })
      .catch(function () {
        showAnswer('Could not reach PULSE. Check your connection and try again.', null, true);
        hint.textContent = 'Answers come from live records.';
      })
      .then(function () { execBtn.disabled = false; });
  }

  /* ── Voice (input only) ─────────────────────────────────────────── */

  function wireMic() {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      micBtn.classList.add('is-unavailable');
      micBtn.disabled = true;
      micBtn.title = 'Speech input is not supported in this browser — type instead';
      return;
    }
    var rec = new SR();
    rec.lang = 'en-IN';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    var listening = false;

    micBtn.addEventListener('click', function () {
      if (listening) { rec.stop(); return; }
      try { rec.start(); } catch (e) { /* already starting */ }
    });

    rec.addEventListener('start', function () {
      listening = true;
      micBtn.classList.add('is-listening');
      hint.classList.remove('is-warning');
      hint.textContent = 'Listening — speak your question.';
    });
    rec.addEventListener('end', function () {
      listening = false;
      micBtn.classList.remove('is-listening');
      hint.textContent = 'Answers come from live records.';
    });
    rec.addEventListener('error', function (e) {
      listening = false;
      micBtn.classList.remove('is-listening');
      hint.classList.add('is-warning');
      hint.textContent = e.error === 'not-allowed'
        ? 'Microphone access was blocked. Allow it in your browser, or type instead.'
        : 'Could not hear that. Try again, or type your question.';
    });
    rec.addEventListener('result', function (e) {
      var said = e.results[0][0].transcript;
      input.value = said;
      ask(said);
    });
  }

  /* ── Wiring ─────────────────────────────────────────────────────── */

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) {
      hint.classList.add('is-warning');
      hint.textContent = 'Type a question first — try "what needs attention".';
      input.focus();
      return;
    }
    ask(q);
  });

  panelClose.addEventListener('click', function () {
    panel.classList.remove('is-open');
    setTimeout(function () { panel.hidden = true; }, 380);
  });

  cards.forEach(function (card) {
    card.addEventListener('click', function () {
      selectCard(card.dataset.card);
    });
  });

  if (projectSel) {
    projectSel.addEventListener('change', function () {
      window.location.search = '?project=' + encodeURIComponent(projectSel.value);
    });
  }

  window.addEventListener('resize', sizeField);

  // Boot
  var bootEl = document.getElementById('pulse-bootstrap');
  var summary = null;
  try { summary = JSON.parse(bootEl.textContent); } catch (e) { summary = null; }

  render(summary);
  if (summary && summary.id && projectSel) projectSel.value = summary.id;

  sizeField();
  if (reduceMotion) {
    drawOrb(0);
    drawField(0);
  } else {
    requestAnimationFrame(frame);
  }

  wireMic();
})();
