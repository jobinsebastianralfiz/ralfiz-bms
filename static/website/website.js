/* Landing page: scroll reveals, mobile menu, product screenshot tabs, demo form preselect. */
(function () {
  'use strict';
  var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };

  // Reveal sections as they scroll in (everything shows at once without IntersectionObserver).
  var items = $$('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el, i) { el.style.transitionDelay = (i % 3) * 80 + 'ms'; io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }

  // Mobile menu
  var burger = document.querySelector('.burger'), links = document.getElementById('navLinks');
  if (burger) {
    burger.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      burger.setAttribute('aria-expanded', open);
    });
    links.addEventListener('click', function (e) { if (e.target.closest('a')) { links.classList.remove('open'); burger.setAttribute('aria-expanded', false); } });
  }

  // Ralfiz Social screenshot tabs, auto-advancing until someone picks one.
  var tabs = $$('.tabs button'), shots = $$('.shots img'), timer;
  function show(i) {
    tabs.forEach(function (t, k) { t.classList.toggle('on', k === i); });
    shots.forEach(function (s, k) { s.classList.toggle('on', k === i); });
  }
  tabs.forEach(function (t, i) { t.addEventListener('click', function () { clearInterval(timer); show(i); }); });
  if (shots.length && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var cur = 0;
    timer = setInterval(function () { cur = (cur + 1) % shots.length; show(cur); }, 3500);
  }

  // Promo video: plays muted while on screen (saves data), tap for sound.
  var vid = document.getElementById('promoVideo'), snd = document.getElementById('promoSound');
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var play = function (v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); };
  if ('IntersectionObserver' in window && !reduce) {
    var vo = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) play(e.target); else e.target.pause(); });
    }, { threshold: 0.35 });
    $$('video.autoloop').forEach(function (v) { vo.observe(v); });
  }
  if (vid) {
    var setSound = function (on) {
      vid.muted = !on;
      snd.classList.toggle('on', on);
      snd.innerHTML = on ? '<i class="fas fa-volume-high"></i> <span>Sound on</span>' : '<i class="fas fa-volume-xmark"></i> <span>Tap for sound</span>';
      snd.setAttribute('aria-label', on ? 'Turn sound off' : 'Turn sound on');
    };
    snd.addEventListener('click', function () {
      var on = vid.muted;
      if (on) { vid.currentTime = 0; }
      setSound(on);
      var p = vid.play(); if (p && p.catch) p.catch(function () {});
    });
    vid.addEventListener('click', function () { snd.click(); });
    // Hero "Watch the 45s video": scroll to the big player and start it with sound.
    $$('[data-watch]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        vid.closest('.social-video').scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
        vid.currentTime = 0; setSound(true); play(vid);
      });
    });
  }

  // "Book a demo" links preselect the product in the form.
  var select = document.getElementById('interest');
  document.addEventListener('click', function (e) {
    var a = e.target.closest('[data-interest]');
    if (a && select) select.value = a.getAttribute('data-interest');
  });
})();
