/* Social Hub: calendar drag-and-drop, composer, small page helpers. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  function csrf() { var m = document.cookie.match(/csrftoken=([^;]+)/); var i = $('input[name=csrfmiddlewaretoken]'); return (i && i.value) || (m && m[1]) || ''; }

  var toastTimer;
  function toast(msg, bad) {
    var t = $('#shToast'); if (!t) return;
    t.textContent = msg; t.classList.toggle('bad', !!bad); t.classList.add('on');
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.classList.remove('on'); }, 3200);
  }

  // Copy buttons (review links)
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-copy]'); if (!b) return;
    var text = b.getAttribute('data-copy');
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
      .then(function () { toast('Link copied'); })
      .catch(function () { window.prompt('Copy this link', text); });
  });

  // "Request changes" reveals the note box in that card
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-changes]'); if (!b) return;
    var box = b.closest('form').querySelector('.sh-changes');
    box.hidden = !box.hidden; if (!box.hidden) box.querySelector('textarea').focus();
  });

  // ---------------------------------------------------------------- calendar drag & drop
  var dragged = null;
  document.addEventListener('dragstart', function (e) {
    var chip = e.target.closest && e.target.closest('.sh-chip[draggable="true"]'); if (!chip) return;
    dragged = chip; chip.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', chip.getAttribute('data-post'));
  });
  document.addEventListener('dragend', function () {
    if (dragged) dragged.classList.remove('dragging'); dragged = null;
    $$('.sh-day.drop').forEach(function (d) { d.classList.remove('drop'); });
  });
  document.addEventListener('dragover', function (e) {
    var day = e.target.closest && e.target.closest('.sh-day'); if (!day || !dragged || day.classList.contains('past')) return;
    e.preventDefault(); e.dataTransfer.dropEffect = 'move';
    $$('.sh-day.drop').forEach(function (d) { if (d !== day) d.classList.remove('drop'); });
    day.classList.add('drop');
  });
  document.addEventListener('drop', function (e) {
    var day = e.target.closest && e.target.closest('.sh-day'); if (!day || !dragged) return;
    e.preventDefault();
    var chip = dragged, url = chip.getAttribute('data-move'), date = day.getAttribute('data-date');
    var body = new FormData(); body.append('date', date);
    fetch(url, { method: 'POST', body: body, credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'fetch' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) { toast(data.error || 'Could not move the post.', true); return; }
        day.insertBefore(chip, day.querySelector('.sh-more, .sh-add'));
        toast(data.message);
        setTimeout(function () { location.reload(); }, 1200);
      })
      .catch(function () { toast('Could not move the post.', true); });
  });

  // ---------------------------------------------------------------- composer
  var Composer = {
    init: function () {
      var form = $('#composer'); if (!form) return;
      this.form = form;
      this.caps = JSON.parse($('#capsData').textContent || '{}');
      this.over = JSON.parse($('#overridesData').textContent || '{}');
      this.ws = JSON.parse($('#wsData').textContent || '{}');
      this.caption = $('#caption');
      this.tab = '';
      this.pv = null;
      this.media = [];
      var self = this;
      var ids = ($('#mediaIds').value || '').split(',').filter(Boolean);
      ids.forEach(function (id) {
        var it = $('.sh-libitem[data-id="' + id + '"]');
        self.media.push({ id: id, url: it ? it.getAttribute('data-url') : '', kind: it ? it.getAttribute('data-kind') : 'image' });
      });
      // One hidden input per account carries its custom caption.
      this.overBox = $('#overrides');
      $$('#picks input').forEach(function (cb) { cb.addEventListener('change', function () { self.render(); }); });
      this.caption.addEventListener('input', function () {
        if (self.tab) self.over[self.tab] = self.caption.value;
        self.render(true);
      });
      $('#libBtn').addEventListener('click', function () { var l = $('#lib'); l.hidden = !l.hidden; });
      $$('.sh-libitem').forEach(function (b) { b.addEventListener('click', function () { self.toggleMedia(b); }); });
      $('#upload').addEventListener('change', function (e) { self.upload(e.target); });
      var tags = $('#addTags');
      if (tags) tags.addEventListener('click', function () {
        self.caption.value = self.caption.value.replace(/\s+$/, '') + '\n\n' + tags.getAttribute('data-tags');
        self.caption.dispatchEvent(new Event('input'));
      });
      var best = $('#bestBtn');
      if (best) best.addEventListener('click', function () {
        var wd = +best.getAttribute('data-weekday'), hr = +best.getAttribute('data-hour') + 1;
        var d = new Date(); d.setHours(0, 0, 0, 0);
        var add = (wd - ((d.getDay() + 6) % 7) + 7) % 7; if (add === 0 && new Date().getHours() >= hr) add = 7;
        d.setDate(d.getDate() + add);
        $('#date').value = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        $('#time').value = String(hr).padStart(2, '0') + ':00';
      });
      form.addEventListener('submit', function () {
        $('#mediaIds').value = self.media.map(function (m) { return m.id; }).join(',');
      });
      this.render();
    },
    picked: function () {
      var self = this;
      return $$('#picks input:checked').map(function (cb) { return Object.assign({ id: cb.value }, self.caps[cb.value]); });
    },
    textFor: function (id) { return (this.over[id] !== undefined && this.over[id] !== '') ? this.over[id] : this.caption.dataset.base !== undefined ? this.caption.dataset.base : this.caption.value; },
    render: function (typing) {
      var self = this, picked = this.picked();
      if (this.tab && !picked.some(function (a) { return a.id === self.tab; })) this.switchTab('');
      var base = this.tab ? this.caption.dataset.base : this.caption.value;
      // tabs
      if (!typing) {
        var tabs = '<button type="button" data-tab="" class="' + (this.tab ? '' : 'on') + '">Main caption</button>';
        picked.forEach(function (a) {
          var custom = self.over[a.id] ? ' custom' : '';
          tabs += '<button type="button" data-tab="' + a.id + '" class="' + (self.tab === a.id ? 'on' : '') + custom + '">' + esc(a.label) + (picked.filter(function (b) { return b.platform === a.platform; }).length > 1 ? ' · ' + esc(a.handle || a.name) : '') + '</button>';
        });
        $('#capTabs').innerHTML = tabs;
        $$('#capTabs button').forEach(function (b) { b.addEventListener('click', function () { self.switchTab(b.getAttribute('data-tab')); }); });
      } else {
        $$('#capTabs button[data-tab]').forEach(function (b) { var id = b.getAttribute('data-tab'); if (id) b.classList.toggle('custom', !!self.over[id]); });
      }
      // hidden override inputs
      this.overBox.innerHTML = picked.map(function (a) {
        return '<input type="hidden" name="override_' + a.id + '" value="' + esc(self.over[a.id] || '') + '">';
      }).join('') + (this.tab && this.over[this.tab] ? '<button type="button" class="sh-reset" id="resetOv">Use the main caption for this platform</button>' : '');
      var reset = $('#resetOv');
      if (reset) reset.addEventListener('click', function () { delete self.over[self.tab]; self.caption.value = base; self.render(); });
      // counters
      $('#counts').innerHTML = picked.map(function (a) {
        var n = (self.over[a.id] || base || '').length, left = a.max_chars - n;
        return '<span class="sh-cnt' + (left < 0 ? ' over' : '') + '" style="--pc:' + a.color + '"><i></i>' + esc(a.label) + ' ' + left.toLocaleString('en-IN') + '</span>';
      }).join('');
      // conditional fields
      $('#titleRow').hidden = !picked.some(function (a) { return a.title; });
      $('#firstRow').hidden = !picked.some(function (a) { return a.first_comment; });
      var go = $('#goBtn'); if (go) go.disabled = !picked.length;
      // media row
      $('#medRow').innerHTML = this.media.map(function (m, i) {
        return '<div class="sh-med">' + (m.kind === 'video' ? '<video src="' + esc(m.url) + '" muted></video>' : '<img src="' + esc(m.url) + '" alt="">') +
          '<button type="button" data-rm="' + i + '" aria-label="Remove">✕</button></div>';
      }).join('');
      $$('#medRow [data-rm]').forEach(function (b) { b.addEventListener('click', function () { self.media.splice(+b.getAttribute('data-rm'), 1); self.syncLib(); self.render(); }); });
      this.warnings(picked, base);
      this.preview(picked, base);
    },
    switchTab: function (id) {
      if (!this.tab) this.caption.dataset.base = this.caption.value;
      this.tab = id;
      if (id) { this.caption.value = this.over[id] || this.caption.dataset.base || ''; }
      else { this.caption.value = this.caption.dataset.base || this.caption.value; delete this.caption.dataset.base; }
      this.caption.name = id ? '' : 'text';
      if (id) this.ensureBaseInput(); else { var h = $('#baseText'); if (h) h.remove(); }
      this.render();
      this.caption.focus();
    },
    ensureBaseInput: function () {
      var h = $('#baseText');
      if (!h) { h = document.createElement('input'); h.type = 'hidden'; h.id = 'baseText'; h.name = 'text'; this.form.appendChild(h); }
      h.value = this.caption.dataset.base || '';
    },
    warnings: function (picked, base) {
      var self = this, out = [];
      var kinds = this.media.map(function (m) { return m.kind; });
      picked.forEach(function (a) {
        var text = self.over[a.id] || base || '';
        if (!a.healthy) out.push(a.label + ': reconnect this account first.');
        if (text.length > a.max_chars) out.push(a.label + ' allows ' + a.max_chars.toLocaleString('en-IN') + ' characters.');
        if (a.requires_media && !self.media.length) out.push(a.label + ' needs ' + (a.images ? 'an image or video' : 'a video') + '.');
        if (self.media.length > a.max_media) out.push(a.label + ' takes at most ' + a.max_media + ' file' + (a.max_media > 1 ? 's' : '') + '.');
        if (kinds.indexOf('video') > -1 && !a.video) out.push(a.label + ' does not take video here.');
        if (kinds.indexOf('image') > -1 && !a.images) out.push(a.label + ' needs a video, not an image.');
        if (a.platform === 'whatsapp') out.push('WhatsApp has no feed. Use the inbox to send templates to customers.');
      });
      var w = $('#warn'); w.hidden = !out.length;
      w.innerHTML = out.filter(function (x, i) { return out.indexOf(x) === i; }).map(esc).join('<br>');
    },
    preview: function (picked, base) {
      var self = this, tabs = $('#pvTabs'), box = $('#preview');
      if (!picked.length) { tabs.innerHTML = ''; box.innerHTML = '<div class="pv-empty">Pick an account to see a preview.</div>'; return; }
      if (!this.pv || !picked.some(function (a) { return a.id === self.pv; })) this.pv = picked[0].id;
      tabs.innerHTML = picked.map(function (a) { return '<button type="button" data-pv="' + a.id + '" class="' + (a.id === self.pv ? 'on' : '') + '">' + esc(a.label) + '</button>'; }).join('');
      $$('#pvTabs button').forEach(function (b) { b.addEventListener('click', function () { self.pv = b.getAttribute('data-pv'); self.render(true); }); });
      var a = picked.filter(function (x) { return x.id === self.pv; })[0];
      var text = esc(this.over[a.id] || base || '') || '<span style="color:#94a3b8">Your caption appears here.</span>';
      var m = this.media[0], title = esc(($('#title') || {}).value || ''), first = esc(($('#first_comment') || {}).value || '');
      var img = function (ratio) {
        return '<div class="pv-img" style="aspect-ratio:' + ratio + '">' + (m ? (m.kind === 'video' ? '<video src="' + esc(m.url) + '" muted></video>' : '<img src="' + esc(m.url) + '" alt="">') : '<i class="far fa-image fa-2x"></i>') + '</div>';
      };
      var av = '<span class="sh-av" style="background:' + esc(this.ws.color) + '">' + esc(this.ws.initial) + '</span>';
      var who = esc(a.handle || a.name), name = esc(this.ws.name), html;
      switch (a.platform) {
        case 'instagram':
          html = '<div class="pv-head">' + av + '<b>' + who.replace(/^@/, '') + '</b></div>' + img('1') +
            '<div class="pv-icons"><i class="far fa-heart"></i><i class="far fa-comment"></i><i class="far fa-paper-plane"></i></div>' +
            '<div class="pv-text clamp"><b>' + who.replace(/^@/, '') + '</b> ' + text + '</div>' + (first ? '<div class="pv-first">' + who.replace(/^@/, '') + ' ' + first + '</div>' : '');
          break;
        case 'facebook':
          html = '<div class="pv-head">' + av + '<div><b>' + name + '</b><small>Scheduled · <i class="fas fa-earth-asia"></i></small></div></div><div class="pv-text">' + text + '</div>' + (m ? img('1.91') : '') +
            '<div class="pv-bar"><span><i class="far fa-thumbs-up"></i> Like</span><span><i class="far fa-comment"></i> Comment</span><span><i class="fas fa-share"></i> Share</span></div>';
          break;
        case 'linkedin':
          html = '<div class="pv-head">' + av + '<div><b>' + name + '</b><small>Company page · now</small></div></div><div class="pv-text clamp">' + text + '</div>' + (m ? img('1.91') : '') +
            '<div class="pv-bar"><span><i class="far fa-thumbs-up"></i> Like</span><span><i class="far fa-comment-dots"></i> Comment</span><span><i class="fas fa-retweet"></i> Repost</span></div>';
          break;
        case 'x':
          html = '<div class="pv-head">' + av + '<div><b>' + name + '</b><small>' + who + '</small></div></div><div class="pv-text">' + text + '</div>' + (m ? '<div style="padding:0 12px 12px">' + img('16/9') + '</div>' : '') +
            '<div class="pv-bar"><span><i class="far fa-comment"></i></span><span><i class="fas fa-retweet"></i></span><span><i class="far fa-heart"></i></span><span><i class="fas fa-chart-simple"></i></span></div>';
          break;
        case 'youtube':
          html = img('16/9') + '<div class="pv-title">' + (title || '<span style="color:#94a3b8">Video title</span>') + '</div><div class="pv-head" style="padding-top:2px">' + av + '<small>' + name + ' · just now</small></div><div class="pv-text clamp" style="color:#64748b">' + text + '</div>';
          break;
        case 'whatsapp':
          html = '<div class="pv-wa"><div class="pv-bubble">' + text + '</div></div>';
          break;
        default:
          html = '<div class="pv-head">' + av + '<div><b>' + name + '</b><small>Update on Google</small></div></div>' + (m ? img('4/3') : '') + '<div class="pv-text clamp">' + text + '</div>' +
            (($('#link') || {}).value ? '<div class="pv-cta">Learn more</div>' : '');
      }
      box.innerHTML = html;
    },
    toggleMedia: function (b) {
      var id = b.getAttribute('data-id'), i = this.media.map(function (m) { return m.id; }).indexOf(id);
      if (i > -1) this.media.splice(i, 1);
      else this.media.push({ id: id, url: b.getAttribute('data-url'), kind: b.getAttribute('data-kind') });
      this.syncLib(); this.render();
    },
    syncLib: function () {
      var ids = this.media.map(function (m) { return m.id; });
      $$('.sh-libitem').forEach(function (b) { b.classList.toggle('on', ids.indexOf(b.getAttribute('data-id')) > -1); });
    },
    upload: function (input) {
      var self = this, files = input.files; if (!files.length) return;
      var body = new FormData(); body.append('workspace', input.getAttribute('data-ws'));
      Array.prototype.forEach.call(files, function (f) { body.append('files', f); });
      toast('Uploading…');
      fetch(input.getAttribute('data-url'), { method: 'POST', body: body, credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'fetch' } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.ok) { toast(data.error || 'Upload failed.', true); return; }
          data.assets.reverse().forEach(function (a) { self.media.push({ id: a.id, url: a.url, kind: a.kind }); });
          input.value = ''; toast('Uploaded'); self.render();
        })
        .catch(function () { toast('Upload failed.', true); });
    }
  };
  window.SocialComposer = Composer;

  // ---------------------------------------------------------------- charts
  window.SocialCharts = {
    trend: function (canvasId, dataId) {
      var el = document.getElementById(canvasId), src = document.getElementById(dataId);
      if (!el || !src || !window.Chart) return;
      var d = JSON.parse(src.textContent);
      new Chart(el, {
        type: 'line',
        data: { labels: d.labels, datasets: [
          { label: 'Reach', data: d.reach, borderColor: '#0ea5e9', backgroundColor: 'rgba(14,165,233,.12)', fill: true, tension: .35, pointRadius: 0, yAxisID: 'y' },
          { label: 'Engagement', data: d.engagement, borderColor: '#8b5cf6', backgroundColor: 'transparent', tension: .35, pointRadius: 0, yAxisID: 'y1' }
        ] },
        options: { maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, usePointStyle: true } } },
          scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
            y: { beginAtZero: true, grid: { color: '#eef2f7' }, ticks: { callback: function (v) { return v >= 1000 ? (v / 1000) + 'K' : v; } } },
            y1: { beginAtZero: true, position: 'right', grid: { display: false } } } }
      });
    }
  };
})();
