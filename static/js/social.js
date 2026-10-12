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
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var kfmt = function (v) { v = Math.round(v); return v >= 100000 ? (v / 100000).toFixed(1) + 'L' : v >= 1000 ? (v / 1000).toFixed(1) + 'K' : String(v); };
  var NS = 'http://www.w3.org/2000/svg';

  // The goal ring on Home fills to its percentage once the page settles.
  $$('.goal-arc').forEach(function (arc) {
    var pct = Math.max(0, Math.min(100, +arc.getAttribute('data-pct') || 0));
    requestAnimationFrame(function () { requestAnimationFrame(function () { arc.style.strokeDashoffset = 502.7 * (1 - pct / 100); }); });
  });

  function lineChart(svg, tip, labels, values, unit) {
    var n = values.length, W = 800, H = 260, L = 46, R = 14, T = 18, B = 30;
    if (!n) { svg.innerHTML = ''; return; }
    var mx = Math.max.apply(null, values.concat([1]));
    var mag = Math.pow(10, Math.floor(Math.log10(mx))), step = mag * (mx / mag > 5 ? 2 : 1), top = Math.ceil(mx / step) * step;
    var X = function (i) { return L + (n === 1 ? 0 : i / (n - 1)) * (W - L - R); }, Y = function (v) { return T + (1 - v / top) * (H - T - B); };
    var pts = values.map(function (v, i) { return [X(i), Y(v)]; });
    var d = 'M' + pts[0][0] + ' ' + pts[0][1];
    for (var i = 1; i < n; i++) { var cx = (pts[i - 1][0] + pts[i][0]) / 2; d += ' C' + cx + ' ' + pts[i - 1][1] + ' ' + cx + ' ' + pts[i][1] + ' ' + pts[i][0] + ' ' + pts[i][1]; }
    var last = pts[n - 1], ticks = [0, .5, 1].map(function (f) { return top * f; });
    var xl = [0, Math.round((n - 1) / 3), Math.round(2 * (n - 1) / 3), n - 1];
    svg.innerHTML = '<defs><linearGradient id="lg" x1="0" x2="1"><stop offset="0" stop-color="#FF7A3D"/><stop offset=".4" stop-color="#FF2E88"/><stop offset=".75" stop-color="#9B4DFF"/><stop offset="1" stop-color="#3D8BFF"/></linearGradient>' +
      '<linearGradient id="ag" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#FF2E88" stop-opacity=".45"/><stop offset="1" stop-color="#9B4DFF" stop-opacity="0"/></linearGradient>' +
      '<filter id="glow"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>' +
      ticks.map(function (t) { return '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(t) + '" y2="' + Y(t) + '" stroke="rgba(255,255,255,.1)" stroke-dasharray="' + (t ? '4 6' : '0') + '" vector-effect="non-scaling-stroke"/><text class="ax" x="' + (L - 8) + '" y="' + (Y(t) + 3.5) + '" text-anchor="end">' + kfmt(t) + '</text>'; }).join('') +
      xl.map(function (i, k) { return '<text class="ax" x="' + X(i) + '" y="' + (H - 9) + '" text-anchor="' + (k === 0 ? 'start' : k === 3 ? 'end' : 'middle') + '">' + esc(labels[i] || '') + '</text>'; }).join('') +
      '<path id="ar" d="' + d + ' L' + X(n - 1) + ' ' + (H - B) + ' L' + L + ' ' + (H - B) + ' Z" fill="url(#ag)" style="opacity:0;transition:opacity 1.2s .4s"/>' +
      '<path id="ln" d="' + d + '" fill="none" stroke="url(#lg)" stroke-width="3.5" stroke-linecap="round" filter="url(#glow)" vector-effect="non-scaling-stroke"/>' +
      '<line id="gl" x1="0" x2="0" y1="' + T + '" y2="' + (H - B) + '" stroke="rgba(255,255,255,.35)" stroke-dasharray="3 4" opacity="0" vector-effect="non-scaling-stroke"/>' +
      '<circle cx="' + last[0] + '" cy="' + last[1] + '" r="5.5" fill="#fff" stroke="#3D8BFF" stroke-width="3"/>' +
      '<circle id="gd" r="7" fill="#fff" stroke="#FF2E88" stroke-width="3.5" opacity="0"/>' +
      '<rect id="hit" x="' + L + '" y="' + T + '" width="' + (W - L - R) + '" height="' + (H - T - B) + '" fill="transparent"/>';
    var ln = svg.querySelector('#ln');
    if (!RM && ln.getTotalLength) { var len = ln.getTotalLength(); ln.style.strokeDasharray = len; ln.style.strokeDashoffset = len; ln.getBoundingClientRect(); ln.classList.add('drawn'); requestAnimationFrame(function () { ln.style.strokeDashoffset = 0; }); }
    requestAnimationFrame(function () { svg.querySelector('#ar').style.opacity = 1; });
    var hit = svg.querySelector('#hit'), gl = svg.querySelector('#gl'), gd = svg.querySelector('#gd');
    hit.addEventListener('pointermove', function (e) {
      var r = svg.getBoundingClientRect(), px = (e.clientX - r.left) / r.width * W;
      var i = Math.max(0, Math.min(n - 1, Math.round((px - L) / (W - L - R) * (n - 1)))), p = pts[i];
      gl.setAttribute('x1', p[0]); gl.setAttribute('x2', p[0]); gl.setAttribute('opacity', 1);
      gd.setAttribute('cx', p[0]); gd.setAttribute('cy', p[1]); gd.setAttribute('opacity', 1);
      tip.innerHTML = '<span style="opacity:.6">' + esc(labels[i]) + '</span><b>' + Math.round(values[i]).toLocaleString('en-IN') + '</b>' + unit;
      tip.style.left = p[0] / W * r.width + 'px'; tip.style.top = p[1] / H * r.height + 'px'; tip.classList.add('on');
    });
    hit.addEventListener('pointerleave', function () { tip.classList.remove('on'); gl.setAttribute('opacity', 0); gd.setAttribute('opacity', 0); });
  }

  window.SocialCharts = {
    home: function (svgId, tipId, dataId, pillsId) {
      var svg = document.getElementById(svgId), src = document.getElementById(dataId);
      if (!svg || !src) return;
      var d = JSON.parse(src.textContent), tip = document.getElementById(tipId);
      var units = { reach: 'people reached', engagement: 'engagements', followers: 'followers' };
      var draw = function (m) { lineChart(svg, tip, d.labels, d[m] || [], units[m]); };
      $$('#' + pillsId + ' button').forEach(function (b) {
        b.addEventListener('click', function () {
          $$('#' + pillsId + ' button').forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
          draw(b.getAttribute('data-m'));
        });
      });
      draw('reach');
    },
    sparks: function (dataId) {
      var src = document.getElementById(dataId); if (!src) return;
      var data = JSON.parse(src.textContent);
      $$('svg.spark').forEach(function (svg, k) {
        var a = data[svg.getAttribute('data-key')] || [];
        if (a.length < 2) return;
        var mn = Math.min.apply(null, a), mx = Math.max.apply(null, a), span = (mx - mn) || 1;
        var p = a.map(function (v, i) { return [i / (a.length - 1) * 200, 42 - (v - mn) / span * 36]; });
        var l = 'M' + p.map(function (q) { return q[0].toFixed(1) + ' ' + q[1].toFixed(1); }).join(' L');
        var c = getComputedStyle(svg.closest('.kt')).getPropertyValue('--kc').trim() || '#FF2E88';
        svg.innerHTML = '<defs><linearGradient id="sg' + k + '" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="' + c + '" stop-opacity=".5"/><stop offset="1" stop-color="' + c + '" stop-opacity="0"/></linearGradient></defs>' +
          '<path d="' + l + ' L200 46 L0 46 Z" fill="url(#sg' + k + ')"/><path class="spl" d="' + l + '" fill="none" stroke="' + c + '" stroke-width="2.5" vector-effect="non-scaling-stroke"/>' +
          '<circle cx="' + p[p.length - 1][0] + '" cy="' + p[p.length - 1][1] + '" r="4" fill="#fff"/>';
        var spl = svg.querySelector('.spl');
        if (!RM && spl.getTotalLength) { var len = spl.getTotalLength(); spl.style.strokeDasharray = len; spl.style.strokeDashoffset = len; spl.getBoundingClientRect(); spl.classList.add('drawn'); requestAnimationFrame(function () { spl.style.strokeDashoffset = 0; }); }
      });
    },
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
