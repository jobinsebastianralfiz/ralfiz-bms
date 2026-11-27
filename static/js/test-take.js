/* Online test page (staff portal): answered counter, autosave to the server,
   countdown with auto-submit, a code editor that takes Tab, and a Run button
   for Python questions (Pyodide, loaded from jsDelivr on first Run).
   Used by assessment_take.html and, after the camera check, proctor.js. */
(function () {
  'use strict';
  var PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js';

  function init(opts) {
    opts = opts || {};
    var form = document.getElementById('mqForm');
    if (!form) return null;
    var total = parseInt(form.dataset.total, 10) || 0;
    var savedLabel = document.getElementById('mqSaved');
    var submitBtn = document.getElementById('mqSubmit');
    var state = { submitting: false, dirty: false, armed: false };

    function answeredCount() {
      var n = 0;
      form.querySelectorAll('fieldset.mq-q').forEach(function (fs) {
        if (fs.dataset.type === 'mcq') { if (fs.querySelector('input:checked')) n++; }
        else {
          var t = fs.querySelector('textarea');
          if (t && t.value.trim() && t.value !== t.dataset.starter) n++;
        }
      });
      return n;
    }
    function refresh() {
      var n = answeredCount();
      document.getElementById('mqAnswered').textContent = n;
      document.getElementById('mqProgress').style.width = (total ? n / total * 100 : 0) + '%';
      document.getElementById('mqLeftNote').textContent = n < total
        ? (total - n) + ' question' + (total - n === 1 ? '' : 's') + ' not answered yet.' : 'All questions answered.';
      if (state.armed) disarm();
    }

    // --- Autosave: a few seconds after the last change, and every 30 s.
    var timer = null;
    function formData() { return new FormData(form); }
    function save() {
      if (state.submitting || !state.dirty) return Promise.resolve();
      state.dirty = false;
      savedLabel.textContent = 'Saving…';
      return fetch(form.dataset.autosave, { method: 'POST', body: formData(), credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.submitted) { window.location.reload(); return; }
          savedLabel.textContent = d.saved ? 'Saved' : 'Not saved';
        })
        .catch(function () { state.dirty = true; savedLabel.textContent = 'Offline, will retry'; });
    }
    function changed() {
      state.dirty = true;
      savedLabel.textContent = 'Unsaved';
      clearTimeout(timer);
      timer = setTimeout(save, 2500);
      refresh();
    }
    form.addEventListener('change', changed);
    form.addEventListener('input', changed);
    setInterval(save, 30000);
    refresh();

    // --- Code editor: Tab indents, Enter keeps the indent.
    form.querySelectorAll('textarea.mq-editor').forEach(function (ta) {
      ta.addEventListener('keydown', function (e) {
        var s = ta.selectionStart, en = ta.selectionEnd, v = ta.value;
        if (e.key === 'Tab') {
          e.preventDefault();
          ta.value = v.slice(0, s) + '    ' + v.slice(en);
          ta.selectionStart = ta.selectionEnd = s + 4;
          changed();
        } else if (e.key === 'Enter') {
          var lineStart = v.lastIndexOf('\n', s - 1) + 1;
          var indent = (v.slice(lineStart, s).match(/^\s*/) || [''])[0];
          if (/:\s*$/.test(v.slice(lineStart, s)) || /[{(\[]\s*$/.test(v.slice(lineStart, s))) indent += '    ';
          if (indent) {
            e.preventDefault();
            ta.value = v.slice(0, s) + '\n' + indent + v.slice(en);
            ta.selectionStart = ta.selectionEnd = s + 1 + indent.length;
            changed();
          }
        }
      });
    });

    // --- Run Python in the browser.
    var pyPromise = null;
    function loadPython() {
      if (pyPromise) return pyPromise;
      pyPromise = new Promise(function (resolve, reject) {
        var sc = document.createElement('script');
        sc.src = PYODIDE_URL;
        sc.onload = function () { window.loadPyodide().then(resolve, reject); };
        sc.onerror = function () { reject(new Error('Could not load Python. Check your internet and try again.')); };
        document.head.appendChild(sc);
      });
      pyPromise.catch(function () { pyPromise = null; });
      return pyPromise;
    }
    form.querySelectorAll('.mq-run').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var ta = form.querySelector('textarea[name="' + btn.dataset.for + '"]');
        var out = document.getElementById('out_' + btn.dataset.for);
        out.hidden = false; out.className = 'mq-run-out';
        out.textContent = pyPromise ? 'Running…' : 'Loading Python (first run only, a few seconds)…';
        btn.disabled = true;
        loadPython().then(function (py) {
          var buf = [];
          py.setStdout({ batched: function (x) { buf.push(x); } });
          py.setStderr({ batched: function (x) { buf.push(x); } });
          py.setStdin({ error: true });
          var ns = py.globals.get('dict')();
          ns.set('__name__', '__main__');
          return py.runPythonAsync(ta.value, { globals: ns }).then(function () {
            out.textContent = buf.join('\n') || '(no output)';
          }, function (err) {
            out.className = 'mq-run-out err';
            var msg = String(err.message || err), i = msg.indexOf('File "<exec>"');
            out.textContent = (buf.length ? buf.join('\n') + '\n\n' : '') + (i > -1 ? 'Traceback:\n  ' + msg.slice(i) : msg);
          }).finally(function () { try { ns.destroy(); } catch (e) {} });
        }, function (err) { out.className = 'mq-run-out err'; out.textContent = err.message; })
          .finally(function () { btn.disabled = false; });
      });
    });

    // --- Submit: no browser confirm() (it steals focus and would lock a
    // proctored test); the first tap warns, the second submits.
    function disarm() {
      state.armed = false;
      submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit test';
      submitBtn.classList.remove('warn');
    }
    form.addEventListener('submit', function (e) {
      if (state.submitting) return;
      var left = total - answeredCount();
      if (left > 0 && !state.armed && !state.force) {
        e.preventDefault();
        state.armed = true;
        submitBtn.innerHTML = '<i class="fas fa-triangle-exclamation"></i> ' + left + ' unanswered · tap again to submit';
        submitBtn.classList.add('warn');
        return;
      }
      state.submitting = true;
      submitBtn.disabled = true;
    });
    function submitNow() {
      if (state.submitting) return;
      state.force = true; state.submitting = true;
      form.submit();
    }
    if (opts.warnOnLeave) {
      window.addEventListener('beforeunload', function (e) {
        if (!state.submitting && state.dirty) { e.preventDefault(); e.returnValue = ''; }
      });
    }

    // --- Countdown.
    var tEl = document.getElementById('mqTimer');
    if (tEl) {
      var ends = Date.now() + parseInt(tEl.dataset.left, 10) * 1000;
      var label = tEl.querySelector('span');
      (function tick() {
        var s = Math.max(0, Math.round((ends - Date.now()) / 1000));
        var h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
        label.textContent = (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(s % 60).padStart(2, '0');
        tEl.classList.toggle('low', s <= 60);
        if (s === 0) { submitNow(); return; }
        setTimeout(tick, 500);
      })();
    }

    return {
      form: form, formData: formData, state: state, submitNow: submitNow,
      stop: function () { state.submitting = true; }
    };
  }

  window.TestTake = { init: init };
})();
