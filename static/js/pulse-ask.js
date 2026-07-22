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
  var speakBtn  = document.getElementById('pulse-speaker');
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

  /* ── Voice output ───────────────────────────────────────────────── */
  /* Read-back is on by default and remembered. The utterance prefers an
     en-IN voice to match the recognition language. */

  var canSpeak = 'speechSynthesis' in window
    && 'SpeechSynthesisUtterance' in window;
  var speakOn = true;
  try { speakOn = localStorage.getItem('pulseSpeak') !== '0'; } catch (e) {}

  function reflectSpeaker() {
    if (speakBtn) speakBtn.classList.toggle('is-off', !speakOn);
  }

  function speak(text) {
    if (!canSpeak || !speakOn || !text) return;
    window.speechSynthesis.cancel();
    var utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-IN';
    var voices = window.speechSynthesis.getVoices();
    for (var i = 0; i < voices.length; i++) {
      if (voices[i].lang && voices[i].lang.replace('_', '-') === 'en-IN') {
        utterance.voice = voices[i];
        break;
      }
    }
    window.speechSynthesis.speak(utterance);
  }

  function hush() {
    if (canSpeak) window.speechSynthesis.cancel();
  }

  if (speakBtn) {
    if (!canSpeak) {
      speakBtn.classList.add('is-unavailable');
      speakBtn.disabled = true;
      speakBtn.title = 'Speech output is not supported in this browser';
    } else {
      reflectSpeaker();
      speakBtn.addEventListener('click', function () {
        speakOn = !speakOn;
        try { localStorage.setItem('pulseSpeak', speakOn ? '1' : '0'); } catch (e) {}
        reflectSpeaker();
        if (!speakOn) hush();
        setHint(speakOn ? 'PULSE will read answers aloud.'
                        : 'PULSE is muted — answers stay on screen.');
      });
    }
  }

  function ask(query) {
    if (execBtn) execBtn.disabled = true;
    hush();
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
          speak(r.body.answer);
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
      hush();
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
        hush();
        try {
          rec.start();
        } catch (e) {
          // A stuck 'already started' session: reset and retry once.
          try { rec.abort(); rec.start(); } catch (e2) {
            show('The microphone could not start. Reload the page and try again.', null, true);
          }
        }
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
        var messages = {
          'not-allowed':
            'Microphone access is blocked for this site. Allow it from the ' +
            'icon in the address bar, reload the page, and try again.',
          'service-not-allowed':
            'The browser refused speech recognition for this site. Check the ' +
            'microphone permission, reload, and try again.',
          'audio-capture':
            'No microphone was found. Plug one in or check your input device.',
          'network':
            'The speech service could not be reached. Check your connection ' +
            'and try again, or type your question.',
          'no-speech':
            'Nothing was heard. Click the mic and speak your question.'
        };
        var message = messages[e.error] ||
          'Speech input failed (' + e.error + '). Try again, or type your question.';
        // The hint line is easy to miss -- put the failure where answers go.
        show(message, 'voice input', true);
        setHint(restingHint);
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
