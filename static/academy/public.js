/* Public catalogue: live simulators, sample exam questions, scroll reveals. */
(function () {
  'use strict';
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };

  // "Try it in your browser": mount each simulator the first time its tab opens.
  var mounted = {};
  function show(sim) {
    $$('.try-tabs [data-sim]').forEach(function (b) { b.setAttribute('aria-selected', String(b.dataset.sim === sim)); });
    $$('.try-pane').forEach(function (p) { p.hidden = p.dataset.pane !== sim; });
    if (!mounted[sim] && window.AcademySims) {
      mounted[sim] = true;
      window.AcademySims.mount($('.try-pane[data-pane="' + sim + '"]'), sim, null, 'public-' + sim);
    }
  }
  $$('.try-tabs [data-sim]').forEach(function (b) { b.onclick = function () { show(b.dataset.sim); }; });
  if ($('.try-tabs')) show('powerfx');

  // "Try a real exam question": graded on the server, one attempt then reveal.
  $$('.sq').forEach(function (card) {
    var opts = $$('.opt', card);
    opts.forEach(function (o) {
      o.onclick = function () {
        if (o.disabled) return;
        opts.forEach(function (x) { x.disabled = true; });
        fetch(card.dataset.url, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ choice: +o.dataset.j })
        }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
          .then(function (r) {
            opts.forEach(function (x) {
              var j = +x.dataset.j;
              x.classList.toggle('right', j === r.answer);
              x.classList.toggle('wrong', j === +o.dataset.j && !r.correct);
            });
            var why = $('.why', card); why.hidden = false;
            var b = $('b', why); b.className = r.correct ? 'ok' : 'no';
            b.textContent = r.correct ? 'Correct.' : 'Not quite.';
            $('.exp', why).textContent = r.explanation;
            $('.sq-more', card).hidden = false;
          })
          .catch(function () { opts.forEach(function (x) { x.disabled = false; }); });
      };
    });
  });

  // Fade sections in as they scroll into view.
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var items = $$('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  }
})();
