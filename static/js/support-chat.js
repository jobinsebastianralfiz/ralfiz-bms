/* Live support chat, used by the client portal (bubble + full page) and the staff inbox.
 *
 * <div class="sc-chat" data-poll="…/poll/" data-send="…/send/" data-me="client|staff"
 *      data-csrf="…" data-fast="3000" data-slow="15000"> with .sc-log, .sc-form, .sc-input inside.
 * Polls `poll?after=<newest>&open=1` while the chat is visible (marks the other side's messages
 * read) and slowly without `open` while hidden, chiming on new messages from the other side.
 * window.scChat(root) returns {setOpen(bool), onUnread(fn)}.
 */
(function () {
  var MUTE = 'scChatMute', ctx = null;

  function unlock() {
    try { ctx = ctx || new (window.AudioContext || window.webkitAudioContext)(); if (ctx.state === 'suspended') ctx.resume(); } catch (e) {}
  }
  ['pointerdown', 'keydown'].forEach(function (ev) { document.addEventListener(ev, unlock, { once: true, capture: true }); });

  function chime() {
    if (localStorage.getItem(MUTE) === '1') return;
    unlock();
    if (!ctx) return;
    var t = ctx.currentTime;
    [[660, 0], [990, 0.13]].forEach(function (n) {
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.type = 'sine'; o.frequency.value = n[0];
      g.gain.setValueAtTime(0.0001, t + n[1]);
      g.gain.exponentialRampToValueAtTime(0.22, t + n[1] + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + n[1] + 0.4);
      o.connect(g); g.connect(ctx.destination); o.start(t + n[1]); o.stop(t + n[1] + 0.45);
    });
  }
  window.scChime = chime;

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function dayLabel(d) {
    var today = new Date(), y = new Date(); y.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return 'Today';
    if (d.toDateString() === y.toDateString()) return 'Yesterday';
    return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  }
  function timeLabel(d) { return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }); }

  window.scChat = function (root) {
    var log = root.querySelector('.sc-log'), form = root.querySelector('.sc-form'), input = root.querySelector('.sc-input');
    var me = root.dataset.me, fast = +root.dataset.fast || 3000, slow = +root.dataset.slow || 15000;
    var after = null, seen = {}, open = root.dataset.open === '1', timer = null, unreadFns = [], lastDay = null, first = true, busy = false;
    var seenNote = root.querySelector('.sc-seen');

    function mine(m) { return me === 'client' ? m.from_client : !m.from_client; }

    function add(m) {
      if (seen[m.id]) return false;
      seen[m.id] = true;
      var empty = log.querySelector('.sc-empty'); if (empty) empty.remove();
      var d = new Date(m.at), day = d.toDateString();
      if (day !== lastDay) { log.appendChild(el('div', 'sc-day', dayLabel(d))); lastDay = day; }
      var row = el('div', 'sc-msg ' + (mine(m) ? 'me' : 'them'));
      if (!mine(m)) row.appendChild(el('div', 'sc-who', m.sender));
      row.appendChild(el('div', 'sc-bubble', m.body));
      row.appendChild(el('div', 'sc-time', timeLabel(d)));
      log.appendChild(row);
      if (!after || m.at > after) after = m.at;
      return true;
    }
    function toBottom() { log.scrollTop = log.scrollHeight; }

    function schedule() { clearTimeout(timer); timer = setTimeout(poll, open && !document.hidden ? fast : slow); }

    function poll() {
      if (busy) return schedule();
      busy = true;
      var q = [];
      if (after) q.push('after=' + encodeURIComponent(after));
      if (open && !document.hidden) q.push('open=1');
      fetch(root.dataset.poll + (q.length ? '?' + q.join('&') : ''), { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          if (!d) return;
          var nearBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 80, incoming = 0;
          d.messages.forEach(function (m) { if (add(m) && !mine(m)) incoming++; });
          if (first) { toBottom(); if (!log.children.length) log.appendChild(el('div', 'sc-empty', root.dataset.empty || 'No messages yet.')); }
          else if (incoming) { if (nearBottom || !open) toBottom(); if (!open || document.hidden) chime(); }
          if (seenNote && 'seen' in d) seenNote.hidden = !d.seen;
          if ('unread' in d) unreadFns.forEach(function (f) { f(d.unread, first ? 0 : incoming, d.messages); });
          first = false;
        })
        .catch(function () {})
        .then(function () { busy = false; schedule(); });
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var body = input.value.trim();
      if (!body) return;
      var btn = form.querySelector('button[type=submit]'); if (btn) btn.disabled = true;
      var fd = new FormData(); fd.append('body', body);
      fetch(root.dataset.send, { method: 'POST', body: fd, credentials: 'same-origin',
        headers: { 'X-CSRFToken': root.dataset.csrf, 'Accept': 'application/json' } })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (!res.ok) { alertBox(res.j.detail || 'Could not send. Try again.'); return; }
          input.value = ''; input.style.height = '';
          add(res.j.message); toBottom();
          if (seenNote) seenNote.hidden = true;
        })
        .catch(function () { alertBox('Could not send. Check your connection and try again.'); })
        .then(function () { if (btn) btn.disabled = false; input.focus(); });
    });
    function alertBox(text) {
      var n = root.querySelector('.sc-error');
      if (!n) { n = el('div', 'sc-error'); form.parentNode.insertBefore(n, form); }
      n.textContent = text;
      setTimeout(function () { n.remove(); }, 5000);
    }
    // Enter sends, Shift+Enter makes a new line; the box grows with the text.
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit')); }
    });
    input.addEventListener('input', function () { input.style.height = ''; input.style.height = Math.min(input.scrollHeight, 140) + 'px'; });
    document.addEventListener('visibilitychange', function () { if (!document.hidden) { clearTimeout(timer); poll(); } });

    poll();
    return {
      setOpen: function (v) { open = v; if (v) { toBottom(); clearTimeout(timer); poll(); setTimeout(function () { input.focus(); }, 50); } },
      onUnread: function (f) { unreadFns.push(f); }
    };
  };
})();
