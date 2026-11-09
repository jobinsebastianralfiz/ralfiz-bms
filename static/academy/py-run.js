/* Run Python examples in the browser (Complete Python Tutorial lessons).
   Every <pre class="code run"> in the lesson gets Run / Edit / Reset / Copy.
   Pyodide (Python compiled to WebAssembly) is fetched from jsDelivr on the
   first Run only, so lessons that are just read cost nothing extra.
   Ported from academy/content/sources/ralfiz-python-tutorial.html. */
(function () {
  'use strict';
  var PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js';
  var blocks = document.querySelectorAll('.deep pre.code.run');
  if (!blocks.length) return;

  var pyPromise = null;
  function loadPython() {
    if (pyPromise) return pyPromise;
    pyPromise = new Promise(function (resolve, reject) {
      var sc = document.createElement('script');
      sc.src = PYODIDE_URL;
      sc.onload = function () { window.loadPyodide().then(resolve, reject); };
      sc.onerror = function () { reject(new Error('Could not load Python. Check your internet connection and try again.')); };
      document.head.appendChild(sc);
    });
    pyPromise.catch(function () { pyPromise = null; });
    return pyPromise;
  }

  function cleanTraceback(msg) {
    var lines = String(msg).split('\n'), idx = -1;
    for (var i = 0; i < lines.length; i++) { if (lines[i].indexOf('File "<exec>"') !== -1) { idx = i; break; } }
    return idx === -1 ? String(msg) : 'Traceback (most recent call last):\n' + lines.slice(idx).join('\n');
  }

  var queue = Promise.resolve();
  function runPython(src, out) {
    out.hidden = false;
    out.className = 'py-out';
    out.textContent = pyPromise ? 'Running…' : 'Loading Python in your browser (first run only, a few seconds)…';
    queue = queue.then(function () {
      return loadPython().then(function (py) {
        var buf = [];
        py.setStdout({ batched: function (s) { buf.push(s); } });
        py.setStderr({ batched: function (s) { buf.push(s); } });
        py.setStdin({ error: true });   // input() needs a real terminal: run those on your computer
        var ns = py.globals.get('dict')();
        ns.set('__name__', '__main__');
        return py.loadPackagesFromImports(src).then(function () {
          return py.runPythonAsync(src, { globals: ns });
        }).then(function () {
          out.textContent = buf.join('\n') || '(no output)';
        }, function (err) {
          out.className = 'py-out err';
          out.textContent = (buf.length ? buf.join('\n') + '\n\n' : '') + cleanTraceback(err.message || err);
        }).finally(function () { try { ns.destroy(); } catch (e) { /* already gone */ } });
      }, function (err) {
        out.className = 'py-out err';
        out.textContent = err.message;
      });
    });
  }

  function button(label, title) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'py-btn';
    b.textContent = label;
    if (title) b.title = title;
    return b;
  }

  Array.prototype.forEach.call(blocks, function (pre) {
    var original = pre.textContent;
    var wrap = document.createElement('div');
    wrap.className = 'py-run';
    var bar = document.createElement('div');
    bar.className = 'py-bar';
    var run = button('▶ Run', 'Run this code');
    run.classList.add('primary');
    var edit = button('Edit', 'Change the code, then run it again');
    var reset = button('Reset', 'Put the original code back');
    var copy = button('Copy');
    var out = document.createElement('pre');
    out.className = 'py-out';
    out.hidden = true;
    out.setAttribute('aria-live', 'polite');
    bar.append(run, edit, reset, copy);
    pre.parentNode.insertBefore(wrap, pre);
    wrap.append(bar, pre, out);

    function stopEditing() {
      pre.removeAttribute('contenteditable');
      pre.classList.remove('editing');
      edit.textContent = 'Edit';
    }
    run.addEventListener('click', function () { runPython(pre.textContent, out); });
    edit.addEventListener('click', function () {
      if (pre.getAttribute('contenteditable')) { stopEditing(); return; }
      pre.textContent = pre.textContent;   // drop any markup before editing
      pre.setAttribute('contenteditable', 'plaintext-only');
      if (pre.contentEditable !== 'plaintext-only') pre.setAttribute('contenteditable', 'true');
      pre.setAttribute('spellcheck', 'false');
      pre.classList.add('editing');
      pre.focus();
      edit.textContent = 'Done';
    });
    reset.addEventListener('click', function () {
      stopEditing();
      pre.textContent = original;
      out.hidden = true;
    });
    copy.addEventListener('click', function () {
      var done = function (ok) { copy.textContent = ok ? 'Copied ✓' : 'Select and copy'; setTimeout(function () { copy.textContent = 'Copy'; }, 1500); };
      try { navigator.clipboard.writeText(pre.textContent).then(function () { done(true); }, function () { done(false); }); } catch (e) { done(false); }
    });
    pre.addEventListener('keydown', function (e) {
      if (!pre.getAttribute('contenteditable')) return;
      if (e.key === 'Tab') { e.preventDefault(); document.execCommand('insertText', false, '    '); }
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); runPython(pre.textContent, out); }
    });
  });
})();
