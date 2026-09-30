/* Ralfiz Academy portal behaviour. Pages render on the server; this adds
 * tabs, saving lab ticks, server-graded quiz answers, test autosave and the
 * exercise-file View/Copy buttons. */
(function () {
  'use strict';
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var csrf = ($('meta[name="csrf-token"]') || {}).content || '';

  function post(url, body) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(body)
    }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  }

  // --- Perks: toasts for XP, level-ups and new badges ------------------------
  var toastBox = $('#toasts'), xpToast = null, xpTimer = null, xpTotal = 0;
  var esc = function (t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; };
  function toast(kind, icon, title, sub, ms) {
    if (!toastBox) return null;
    var el = document.createElement('div');
    el.className = 'toast ' + kind;
    el.innerHTML = '<span class="ti">' + icon + '</span><div><b>' + esc(title) + '</b>' +
      (sub ? '<span class="s">' + esc(sub) + '</span>' : '') + '</div>';
    toastBox.appendChild(el);
    el._close = function () { el.classList.add('out'); setTimeout(function () { el.remove(); }, 300); };
    el._timer = setTimeout(el._close, ms || 4000);
    return el;
  }
  function badgeToasts(list) {
    (list || []).forEach(function (b, i) {
      setTimeout(function () {
        toast('badge', '<i class="fa-solid ' + esc(b.icon) + '"></i>', 'Badge earned: ' + b.name, 'See it on your profile', 6000);
      }, i * 400);
    });
  }
  window.academyPerks = function (p) {
    if (!p) return;
    if (p.xp_gain > 0) {
      // Rapid ticks add up in one toast instead of stacking.
      if (xpToast && xpToast.isConnected) { xpTotal += p.xp_gain; clearTimeout(xpToast._timer); }
      else { xpTotal = p.xp_gain; xpToast = toast('xp', '', '', '', 2500); }
      xpToast.querySelector('.ti').textContent = '+' + xpTotal;
      xpToast.querySelector('div').innerHTML = '<b>+' + xpTotal + ' XP</b><span class="s">' + p.xp + ' XP total · ' + esc(p.level) + '</span>';
      xpToast._timer = setTimeout(xpToast._close, 2500);
    }
    if (p.level_up) toast('lvl', '<i class="fa-solid fa-star"></i>', 'Level up: ' + p.level, 'Keep going!', 6000);
    badgeToasts(p.new_badges);
  };
  var nb = $('#newBadges');
  if (nb) { try { badgeToasts(JSON.parse(nb.textContent)); } catch (e) {} }

  // --- Shell: sidebar drawer, track switcher, theme -------------------------
  var side = $('#side'), scrim = $('#scrim'), menuBtn = $('#menuBtn');
  function closeMenu() {
    if (!side) return;
    side.classList.remove('open'); scrim.classList.remove('open');
    if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
  }
  if (menuBtn) menuBtn.onclick = function () {
    var o = !side.classList.contains('open');
    side.classList.toggle('open', o); scrim.classList.toggle('open', o);
    menuBtn.setAttribute('aria-expanded', String(o));
  };
  if (scrim) scrim.onclick = closeMenu;
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
  // Only the mobile drawer scrolls on its own; on desktop scrollIntoView would move the page.
  var cur = side && side.querySelector('a[aria-current="page"]');
  if (cur && side.scrollHeight > side.clientHeight + 1) side.scrollTop = cur.offsetTop - side.clientHeight / 2;

  // Side columns stay on the page scroll (no second scrollbar). One taller than the
  // window pins by its bottom edge instead of its top, so all of it is still reachable.
  var pinned = document.querySelectorAll('.side2, .rail2');
  function pin() {
    pinned.forEach(function (el) {
      el.style.top = '';
      var base = parseFloat(getComputedStyle(el).top) || 0;
      el.style.top = Math.min(base, window.innerHeight - el.offsetHeight) + 'px';
    });
  }
  if (pinned.length) {
    pin();
    window.addEventListener('resize', pin);
    if (window.ResizeObserver) { var ro = new ResizeObserver(pin); pinned.forEach(function (el) { ro.observe(el); }); }
  }

  var trackSel = $('#trackSel');
  if (trackSel) trackSel.onchange = function () {
    location.href = trackSel.dataset.base.replace('TRACK', trackSel.value);
  };

  // Theme: light / dark buttons; no choice saved means follow the system.
  var themeBtns = $$('[data-theme-set]');
  var paintTheme = function () {
    var root = document.documentElement, set = root.getAttribute('data-theme');
    var dark = set ? set === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    themeBtns.forEach(function (b) { b.setAttribute('aria-pressed', String((b.dataset.themeSet === 'dark') === dark)); });
  };
  themeBtns.forEach(function (b) {
    b.onclick = function () {
      document.documentElement.setAttribute('data-theme', b.dataset.themeSet);
      try { localStorage.setItem('academy-theme', b.dataset.themeSet); } catch (e) {}
      paintTheme();
    };
  });
  paintTheme();

  // Course filter chips (dashboard, My Courses).
  $$('[data-filter-for]').forEach(function (group) {
    var grid = document.getElementById(group.dataset.filterFor);
    $$('button', group).forEach(function (b) {
      b.onclick = function () {
        $$('button', group).forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        $$('[data-state]', grid).forEach(function (card) {
          card.hidden = b.dataset.f !== 'all' && card.dataset.state !== b.dataset.f;
        });
      };
    });
  });

  // Track page: expand or collapse every skill area.
  var expandAll = $('#expandAll');
  if (expandAll) expandAll.onclick = function () {
    var areas = $$('#skillAreas details');
    var open = !areas.every(function (d) { return d.open; });
    areas.forEach(function (d) { d.open = open; });
    $('span', expandAll).textContent = open ? 'Collapse all' : 'Expand all';
  };

  document.addEventListener('click', function (e) {
    var who = $('.who[open]');
    if (who && !who.contains(e.target)) who.removeAttribute('open');
  });

  // --- Exercise files --------------------------------------------------------
  function copyText(text, btn, pre) {
    var done = function () { var o = btn.textContent; btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = o; }, 1500); };
    var fallback = function () {
      pre.hidden = false;
      var r = document.createRange(); r.selectNodeContents(pre); var s = getSelection(); s.removeAllRanges(); s.addRange(r);
      btn.textContent = 'Selected: press Ctrl+C';
    };
    try { navigator.clipboard.writeText(text).then(done, fallback); } catch (e) { fallback(); }
  }
  $$('.flist > li').forEach(function (li) {
    var pre = $('.fview', li), view = $('[data-file-view]', li), copy = $('[data-file-copy]', li);
    if (view) view.onclick = function () {
      pre.hidden = !pre.hidden; view.setAttribute('aria-expanded', String(!pre.hidden));
      view.textContent = pre.hidden ? 'View' : 'Hide';
    };
    if (copy) copy.onclick = function () { copyText(pre.textContent, copy, pre); };
  });

  // --- Lesson ----------------------------------------------------------------
  var root = $('#lessonRoot');
  if (root) {
    var tabs = $$('[role=tab]', root), panels = $$('.tabpanel', root);
    var showTab = function (name, scroll) {
      tabs.forEach(function (t) { t.setAttribute('aria-selected', String(t.dataset.tab === name)); });
      panels.forEach(function (p) { p.hidden = p.dataset.panel !== name; });
      $$('[data-rtoc]').forEach(function (o) { o.hidden = o.dataset.rtoc !== name; });
      try { history.replaceState(null, '', location.pathname + (name === 'learn' ? '' : '?tab=' + name)); } catch (e) {}
      if (scroll) window.scrollTo({ top: 0 });
      if (name === 'lab') mountWidget();
    };
    tabs.forEach(function (t) { t.onclick = function () { showTab(t.dataset.tab, false); }; });
    $$('[data-go-tab]', root).forEach(function (b) { b.onclick = function () { showTab(b.dataset.goTab, true); }; });

    var applyStatus = function (st) {
      if (!st) return;
      $('#subLab').textContent = st.lab_ticked;
      var set = function (sel, v) { var el = $(sel); if (el) el.textContent = v; };
      set('#stepsDone', st.lab_ticked);
      set('#railLabN', st.lab_ticked);
      set('#railQuizN', st.quiz_right);
      var total = st.lab_total + st.quiz_total;
      var pct = total ? Math.round((st.lab_ticked + st.quiz_right) / total * 100) : 0;
      set('#railPct', pct + '%');
      if ($('#railBar')) $('#railBar').style.width = pct + '%';
      if ($('#railLab')) $('#railLab').classList.toggle('on', st.lab_done);
      if ($('#railQuiz')) $('#railQuiz').classList.toggle('on', st.quiz_done);
      $('#subQuiz').textContent = st.quiz_right;
      $('#ckLab').hidden = !st.lab_done;
      $('#ckQuiz').hidden = !st.quiz_done;
      var badge = $('#subStatus');
      badge.className = 'pill ' + (st.status === 'done' ? 'ok' : st.status === 'in_progress' ? 'lab' : '');
      badge.textContent = st.status === 'done' ? 'Complete' : st.status === 'in_progress' ? 'In progress' : 'Not started';
      var dot = $('[data-dot="' + root.dataset.lesson + '"]');
      if (dot) dot.className = 'dot ' + (st.status === 'done' ? 'done' : st.status === 'in_progress' ? 'half' : '');
      $('#labMsg').innerHTML = st.lab_done ? '<div class="labdone">Lab complete. ' +
        (st.quiz_done ? 'This lesson is finished.' : 'Now take the quiz to finish the lesson.') + '</div>' : '';
      $('#quizMsg').innerHTML = st.quiz_done && st.quiz_total ? '<div class="labdone">' +
        (st.lab_done ? 'Quiz passed. This lesson is finished.' : 'Quiz passed. Finish the lab steps to complete the lesson.') + '</div>' : '';
    };

    // Lab ticks: save the whole set each time, so the last write wins.
    var boxes = $$('#steps input[type=checkbox]');
    var saveTicks = function () {
      var ticked = boxes.filter(function (b) { return b.checked; }).map(function (b) { return +b.dataset.k; });
      post(root.dataset.labUrl, { ticked_steps: ticked })
        .then(function (r) { applyStatus(r.status); window.academyPerks(r.perks); })
        .catch(function () { $('#labMsg').innerHTML = '<div class="flash error">Could not save. Check your connection and tick again.</div>'; });
    };
    boxes.forEach(function (b) { b.onchange = saveTicks; });

    // Quiz: graded on the server; the key only comes back after an answer.
    var paintQuestion = function (q, chosen, answer, explanation) {
      var right = chosen === answer;
      $$('.opt', q).forEach(function (o) {
        var j = +o.dataset.j;
        o.disabled = true;
        o.classList.toggle('right', j === answer);
        o.classList.toggle('wrong', j === chosen && !right);
      });
      var why = $('.why', q);
      why.hidden = false;
      var b = $('b', why);
      b.className = right ? 'ok' : 'no';
      b.textContent = right ? 'Correct.' : 'Not quite.';
      if (explanation !== undefined) $('.exp', why).textContent = explanation;
      $('.retry', why).hidden = right;
    };
    var resetQuestion = function (q) {
      $$('.opt', q).forEach(function (o) { o.disabled = false; o.classList.remove('right', 'wrong'); });
      $('.why', q).hidden = true;
    };
    var alertBox = function (q, msg) {
      var why = $('.why', q); why.hidden = false;
      $('b', why).className = 'no'; $('b', why).textContent = msg; $('.exp', why).textContent = '';
    };
    $$('.q[data-qid]', root).forEach(function (q) {
      if (q.dataset.chosen !== undefined) paintQuestion(q, +q.dataset.chosen, +q.dataset.answer);
      $$('.opt', q).forEach(function (o) {
        o.onclick = function () {
          if (o.disabled) return;
          $$('.opt', q).forEach(function (x) { x.disabled = true; });
          post(q.dataset.url, { choice: +o.dataset.j })
            .then(function (r) { paintQuestion(q, +o.dataset.j, r.answer, r.explanation); applyStatus(r.status); window.academyPerks(r.perks); })
            .catch(function () { resetQuestion(q); alertBox(q, 'Could not check that answer. Try again.'); });
        };
      });
      $('.retry', q).onclick = function () { resetQuestion(q); };
    });

    // Highlight the section being read in the right-hand "On this page".
    if ('IntersectionObserver' in window) {
      var links = $$('.rtoc a');
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          links.forEach(function (a) { a.classList.toggle('on', a.getAttribute('href') === '#' + en.target.id); });
        });
      }, { rootMargin: '-80px 0px -70% 0px' });
      links.forEach(function (a) {
        var t = document.getElementById(a.getAttribute('href').slice(1));
        if (t) io.observe(t);
      });
    }

    // Simulators load only on lessons that have one.
    var mounted = false;
    var mountWidget = function () {
      var el = $('#widget');
      if (mounted || !el || !window.AcademySims) return;
      mounted = true;
      var data = $('#sorterData');
      window.AcademySims.mount(el, el.dataset.widget, data ? JSON.parse(data.textContent) : null, root.dataset.lesson);
    };
    window.addEventListener('load', function () { if (!$('[data-panel="lab"]').hidden) mountWidget(); });
  }

  // --- Practice test ---------------------------------------------------------
  var form = $('#testForm');
  if (form) {
    var total = +form.dataset.total, timer = null, dirty = false;
    var refresh = function () {};  // the CBT palette replaces this
    var answers = function () {
      var out = {};
      $$('input[type=hidden][name^="q"]', form).forEach(function (inp) {
        if (inp.value !== '') out[inp.name.slice(1)] = +inp.value;
      });
      return out;
    };
    var saved = $('#tSaved');
    var flush = function () {
      if (!dirty) return;
      dirty = false;
      saved.textContent = 'Saving…';
      post(form.dataset.saveUrl, { answers: answers() })
        .then(function () { saved.textContent = 'Saved'; })
        .catch(function () { saved.textContent = 'Not saved yet, will retry'; dirty = true; });
    };
    $$('.q', form).forEach(function (q) {
      var i = q.dataset.i, input = $('input[name="q' + i + '"]', q);
      $$('.opt', q).forEach(function (o) {
        o.onclick = function () {
          input.value = o.dataset.j;
          $$('.opt', q).forEach(function (x) {
            var on = x === o; x.classList.toggle('sel', on); x.setAttribute('aria-checked', String(on));
          });
          var nav = $('[data-qnav="' + i + '"]'); if (nav) nav.classList.add('on');
          var n = Object.keys(answers()).length;
          $('#tCount').textContent = n + ' of ' + total + ' answered';
          dirty = true; clearTimeout(timer); timer = setTimeout(flush, 800);
          refresh();
        };
      });
    });
    var timesUp = false;
    form.addEventListener('submit', function (e) {
      var n = Object.keys(answers()).length;
      if (!timesUp && n < total && !confirm(n + ' of ' + total + ' answered. Submit anyway? Unanswered questions count as wrong.')) {
        e.preventDefault();
      }
    });
    window.addEventListener('pagehide', flush);

    // Timed pattern paper: count down from the server's remaining time, submit at zero.
    var clock = $('#tTimer');
    if (clock) {
      var end = Date.now() + (+clock.dataset.seconds) * 1000, shown = $('b', clock);
      var tick = function () {
        var left = Math.max(0, Math.round((end - Date.now()) / 1000));
        var h = Math.floor(left / 3600), m = Math.floor(left % 3600 / 60), sec = left % 60;
        shown.textContent = (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(sec).padStart(2, '0');
        clock.classList.toggle('low', left <= 300);
        if (left === 0) {
          timesUp = true;
          form.submit();
          return;
        }
        setTimeout(tick, 250);
      };
      tick();
    }

    // CBT screen (like the NTA exam): one question at a time, a palette coloured by status,
    // Save & next, Mark for review & next, Clear response and Previous. Visited and
    // marked-for-review are kept in this browser only; answers are saved to the server.
    var cbt = $('#cbt');
    if (cbt) {
      var qs = $$('.q', form), cur = 0, key = 'cbt:' + cbt.dataset.attempt;
      var state = { visited: [], review: [], cur: 0 };
      try { state = Object.assign(state, JSON.parse(localStorage.getItem(key)) || {}); } catch (e) {}
      var visited = new Set(state.visited), review = new Set(state.review);
      var keep = function () {
        try { localStorage.setItem(key, JSON.stringify({ visited: [...visited], review: [...review], cur: cur })); } catch (e) {}
      };
      var answered = function (i) { return $('input[name="q' + qs[i].dataset.i + '"]', qs[i]).value !== ''; };
      cbt.classList.add('cbt-on');
      $$('.cbt-actions, .pal-legend, .pal-submit, .pal-toggle', cbt).forEach(function (el) { el.hidden = false; });
      refresh = function () {
        var n = { answered: 0, notanswered: 0, notvisited: 0, review: 0, reviewanswered: 0 };
        qs.forEach(function (q, i) {
          var a = answered(i), r = review.has(i), v = visited.has(i) || i === cur;
          var st = r ? (a ? 'reviewanswered' : 'review') : a ? 'answered' : v ? 'notanswered' : 'notvisited';
          n[st]++;
          var link = $('[data-qnav="' + q.dataset.i + '"]', cbt);
          link.className = { answered: 'pa', notanswered: 'pn', notvisited: 'pv', review: 'pr', reviewanswered: 'pra' }[st] + (i === cur ? ' cur' : '');
          link.setAttribute('aria-current', i === cur ? 'true' : 'false');
        });
        Object.keys(n).forEach(function (k) { var el = $('[data-n="' + k + '"]', cbt); if (el) el.textContent = n[k]; });
        $('.pal-count', cbt).textContent = (n.answered + n.reviewanswered) + '/' + total;
        $('[data-act="prev"]', cbt).disabled = cur === 0;
        $('[data-act="next"]', cbt).innerHTML = cur === qs.length - 1
          ? 'Save <i class="fa-solid fa-check"></i>' : 'Save &amp; next <i class="fa-solid fa-arrow-right"></i>';
      };
      var show = function (i, scroll) {
        visited.add(cur);
        cur = Math.max(0, Math.min(qs.length - 1, i));
        visited.add(cur);
        qs.forEach(function (q, k) { q.classList.toggle('cur', k === cur); });
        refresh(); keep(); flush();
        cbt.classList.remove('pal-open');
        if (scroll !== false) {
          var top = cbt.getBoundingClientRect().top + window.scrollY - 90;
          if (window.scrollY > top) window.scrollTo({ top: top });
        }
      };
      cbt.addEventListener('click', function (e) {
        var link = e.target.closest('[data-qnav]');
        if (link) {
          e.preventDefault();
          show(qs.findIndex(function (q) { return q.dataset.i === link.dataset.qnav; }));
          return;
        }
        var btn = e.target.closest('[data-act]');
        if (!btn) return;
        var act = btn.dataset.act;
        if (act === 'next') show(cur + 1);
        else if (act === 'prev') show(cur - 1);
        else if (act === 'review') { review.add(cur); show(cur + 1); }
        else if (act === 'clear') {
          var q = qs[cur];
          $('input[type=hidden]', q).value = '';
          $$('.opt', q).forEach(function (x) { x.classList.remove('sel'); x.setAttribute('aria-checked', 'false'); });
          $('#tCount').textContent = Object.keys(answers()).length + ' of ' + total + ' answered';
          dirty = true; flush(); refresh();
        }
      });
      // Choosing an answer on a question marked for review keeps the mark (NTA's "answered and marked").
      $('.pal-toggle', cbt).addEventListener('click', function () { cbt.classList.toggle('pal-open'); });
      document.addEventListener('keydown', function (e) {
        if (e.target.closest('input, textarea, select') || e.altKey || e.ctrlKey || e.metaKey) return;
        if (e.key === 'ArrowRight') show(cur + 1);
        else if (e.key === 'ArrowLeft') show(cur - 1);
      });
      var start = location.hash ? qs.findIndex(function (q) { return '#' + q.id === location.hash; }) : -1;
      show(start >= 0 ? start : Math.min(state.cur || 0, qs.length - 1), false);
    }
  }
})();
