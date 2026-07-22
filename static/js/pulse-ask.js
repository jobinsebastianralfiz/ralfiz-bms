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

  /* The recogniser must not hear PULSE's own voice; the mic section fills
     these in to pause/resume around each utterance. */
  var voiceCtl = { pause: function () {}, resume: function () {} };

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
    utterance.onstart = voiceCtl.pause;
    utterance.onend = voiceCtl.resume;
    utterance.onerror = voiceCtl.resume;
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

  /* ── Voice input: always listening, wake word "Pulse" ───────────── */
  /* The engine runs continuously (mic button is a mute toggle, on by
     default). Speech that begins with the wake word becomes a query;
     everything else is ignored. A centre overlay animates while words are
     being captured, and the recogniser pauses while PULSE reads an answer
     so it never hears itself. */

  if (micBtn) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      micBtn.classList.add('is-unavailable');
      micBtn.disabled = true;
      micBtn.title = 'Speech input is not supported in this browser — type instead';
    } else {
      var rec = new SR();
      rec.lang = 'en-IN';
      rec.continuous = true;
      rec.interimResults = true;
      rec.maxAlternatives = 1;

      //: Common (mis)hearings of the wake word, anchored to the start.
      var WAKE = /^\s*(?:hey\s+|ok\s+|okay\s+)?(?:pulse|puls|pols|paulse|pulls|paul's)\b[\s,.:;!-]*/i;

      var live = true;          // the user wants the mic hot
      try { live = localStorage.getItem('pulseLive') !== '0'; } catch (e) {}
      var running = false;      // the engine is actually running
      var suspended = false;    // paused while PULSE speaks
      var restartTimer = null;

      /* Centre stage animation, built here so every page gets it free. */
      var overlay = document.createElement('div');
      overlay.className = 'pulse-voice';
      overlay.hidden = true;
      overlay.innerHTML =
        '<div class="pulse-voice__rings" aria-hidden="true">' +
          '<span></span><span></span><span></span>' +
          '<i class="pulse-voice__core"></i>' +
          '<svg viewBox="0 0 20 20"><rect x="7.4" y="2.5" width="5.2" height="9" rx="2.6"/>' +
          '<path d="M4.5 9.2a5.5 5.5 0 0 0 11 0M10 14.7v2.8"/></svg>' +
        '</div>' +
        '<p class="pulse-voice__text"></p>' +
        '<p class="pulse-voice__hint">Listening &mdash; tap anywhere to dismiss</p>';
      document.body.appendChild(overlay);
      var overlayText = overlay.querySelector('.pulse-voice__text');

      function showOverlay(text) {
        overlayText.textContent = text || 'Listening…';
        overlay.hidden = false;
      }
      function hideOverlay() { overlay.hidden = true; }
      overlay.addEventListener('click', function () {
        hideOverlay();
        stopRec();          // drops the current phrase; end handler revives
      });

      function startRec() {
        if (running || suspended || !live) return;
        try { rec.start(); } catch (e) { /* already starting */ }
      }
      function stopRec() {
        try { rec.abort(); } catch (e) { /* not running */ }
      }

      function reflectMic() {
        micBtn.classList.toggle('is-listening', live);
        micBtn.title = live
          ? 'Always listening — say "Pulse, …". Click to mute the mic.'
          : 'Voice is off — click to start listening.';
      }

      voiceCtl.pause = function () {
        suspended = true;
        stopRec();
      };
      voiceCtl.resume = function () {
        suspended = false;
        startRec();
      };

      rec.addEventListener('start', function () { running = true; });

      rec.addEventListener('end', function () {
        running = false;
        hideOverlay();
        // Engines give up after silence; quietly come back.
        if (live && !suspended) {
          clearTimeout(restartTimer);
          restartTimer = setTimeout(startRec, 400);
        }
      });

      rec.addEventListener('error', function (e) {
        running = false;
        if (e.error === 'no-speech' || e.error === 'aborted') return;
        hideOverlay();
        var messages = {
          'not-allowed':
            'Microphone access is blocked for this site. Allow it from the ' +
            'icon in the address bar, then click the mic to listen again.',
          'service-not-allowed':
            'The browser refused speech recognition for this site. Check the ' +
            'microphone permission, then click the mic to listen again.',
          'audio-capture':
            'No microphone was found. Plug one in or check your input device.',
          'network':
            'The speech service could not be reached. Voice is off for now — ' +
            'click the mic to retry, or type your question.'
        };
        // A hard failure would otherwise retry in a loop: switch off and say so.
        live = false;
        try { localStorage.setItem('pulseLive', '0'); } catch (e2) {}
        reflectMic();
        show(messages[e.error] ||
          'Speech input failed (' + e.error + '). Click the mic to retry, ' +
          'or type your question.', null, true);
      });

      rec.addEventListener('result', function (e) {
        var interim = '', finals = '';
        for (var i = e.resultIndex; i < e.results.length; i++) {
          var piece = e.results[i][0].transcript;
          if (e.results[i].isFinal) finals += piece;
          else interim += piece;
        }
        if (interim.trim()) showOverlay(interim.trim());
        if (!finals.trim()) return;

        var heard = finals.trim();
        var wake = WAKE.exec(heard);
        if (!wake) { hideOverlay(); return; }   // not for us
        var query = heard.slice(wake[0].length).trim();
        hideOverlay();
        if (!query) {
          setHint('Heard "Pulse" — say the whole question in one go, like ' +
                  '"Pulse, what are we owed".', true);
          return;
        }
        input.value = query;
        ask(query);
      });

      function goLive() {
        live = true;
        try { localStorage.setItem('pulseLive', '1'); } catch (e) {}
        reflectMic();
        startRec();
        restingHint = 'Say "Pulse, …" then your question — or type it here.';
        setHint(restingHint);
      }

      micBtn.addEventListener('click', function () {
        // A dead-looking mic must never be muted further by the click meant
        // to fix it: only an actually-running engine toggles off. Starting
        // from a real click also forces the permission prompt that an
        // automatic page-load start is allowed to suppress.
        if (!live || !running) { goLive(); return; }
        live = false;
        try { localStorage.setItem('pulseLive', '0'); } catch (e) {}
        reflectMic();
        hideOverlay();
        stopRec();
        setHint('Voice is off. Click the mic to listen again.');
      });

      reflectMic();
      if (live) {
        var canQuery = navigator.permissions && navigator.permissions.query;
        if (canQuery) {
          navigator.permissions.query({ name: 'microphone' }).then(function (st) {
            if (st.state === 'granted') {
              goLive();
            } else if (st.state === 'denied') {
              show('Microphone access is blocked for this site. Allow it '
                   + 'from the icon in the address bar (and check the system '
                   + 'microphone setting for your browser), then click the mic.',
                   null, true);
            } else {
              // Browsers may quietly swallow a prompt we trigger without a
              // click, so ask for one instead of pretending to listen.
              setHint('Click the mic once to allow the microphone — voice '
                      + 'stays hands-free after that.', true);
            }
            st.onchange = function () {
              if (st.state === 'granted' && live) goLive();
            };
          }).catch(function () { goLive(); });
        } else {
          goLive();
        }
      }
    }
  }

  window.pulseAsk = ask;
})();
