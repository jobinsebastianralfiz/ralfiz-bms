/* ==========================================================================
   PULSE command bar — shared by every PULSE screen.

   Owns the question box, the mic, and the response panel. Knows nothing about
   what the page renders behind it, so the command centre and the portfolio
   constellation both load this one file.

   A page can opt into reacting to answers by defining window.pulseOnAnswer,
   which receives the parsed {answer, intent, data}.
   ========================================================================== */

(function () {
  'use strict';

  var form      = document.getElementById('pulse-form');
  var input     = document.getElementById('pulse-input');
  var execBtn   = document.getElementById('pulse-execute');
  var micBtn    = document.getElementById('pulse-mic');
  var hint      = document.getElementById('pulse-hint');
  var panel     = document.getElementById('pulse-response');
  var body      = document.getElementById('pulse-response-body');
  var intentEl  = document.getElementById('pulse-response-intent');
  var closeBtn  = document.getElementById('pulse-response-close');

  if (!form || !input) return;

  var restingHint = hint ? hint.textContent : '';

  function csrf() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function setHint(text, warn) {
    if (!hint) return;
    hint.textContent = text;
    hint.classList.toggle('is-warning', !!warn);
  }

  function show(text, intent, isError) {
    if (!panel) return;
    intentEl.textContent = isError
      ? 'Could not answer'
      : (intent ? intent.replace(/_/g, ' ') : 'Answer');
    body.textContent = text;
    panel.classList.toggle('is-error', !!isError);
    panel.hidden = false;
    requestAnimationFrame(function () { panel.classList.add('is-open'); });
  }

  function ask(query) {
    if (execBtn) execBtn.disabled = true;
    setHint('Working through live records…');

    fetch('/api/pulse/ask/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      credentials: 'same-origin',
      body: JSON.stringify({ query: query })
    })
      .then(function (res) {
        return res.json()
          .catch(function () { return {}; })
          .then(function (b) { return { status: res.status, body: b }; });
      })
      .then(function (r) {
        if (r.status === 200) {
          show(r.body.answer || 'No answer came back.', r.body.intent, false);
          if (typeof window.pulseOnAnswer === 'function') {
            try { window.pulseOnAnswer(r.body); } catch (e) { /* page hook failed */ }
          }
        } else {
          show({
            400: 'That question could not be turned into a query. Try naming the project or date differently.',
            403: 'Your account cannot read business-wide data. PULSE is limited to owner and partner accounts.',
            503: 'PULSE is not configured yet — ANTHROPIC_API_KEY is missing on the server.'
          }[r.status] || (r.body.detail || 'Something went wrong reaching PULSE.'), null, true);
        }
        setHint(restingHint);
      })
      .catch(function () {
        show('Could not reach PULSE. Check your connection and try again.', null, true);
        setHint(restingHint);
      })
      .then(function () { if (execBtn) execBtn.disabled = false; });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) {
      setHint('Type a question first — try "what needs attention".', true);
      input.focus();
      return;
    }
    ask(q);
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      panel.classList.remove('is-open');
      setTimeout(function () { panel.hidden = true; }, 380);
    });
  }

  /* ── Voice input ────────────────────────────────────────────────── */

  if (micBtn) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      micBtn.classList.add('is-unavailable');
      micBtn.disabled = true;
      micBtn.title = 'Speech input is not supported in this browser — type instead';
    } else {
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
        setHint('Listening — speak your question.');
      });
      rec.addEventListener('end', function () {
        listening = false;
        micBtn.classList.remove('is-listening');
        setHint(restingHint);
      });
      rec.addEventListener('error', function (e) {
        listening = false;
        micBtn.classList.remove('is-listening');
        setHint(e.error === 'not-allowed'
          ? 'Microphone access was blocked. Allow it in your browser, or type instead.'
          : 'Could not hear that. Try again, or type your question.', true);
      });
      rec.addEventListener('result', function (e) {
        var said = e.results[0][0].transcript;
        input.value = said;
        ask(said);
      });
    }
  }

  window.pulseAsk = ask;
})();
