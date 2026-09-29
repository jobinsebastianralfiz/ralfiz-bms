const PLAYERS = [
  { name: 'Anu', score: 120 }, { name: 'Rahul', score: 110 }, { name: 'Fatima', score: 95 },
  { name: 'Joel', score: 90 }, { name: 'Meera', score: 70 }, { name: 'Arjun', score: 60 },
];
const MAX = 600;
const QUIZ_MS = 90_000;
const board = document.querySelector('#board');
const clock = document.querySelector('#clock');
const rows = new Map();
const frames = new WeakMap();                 // element → running rAF id
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
let endAt = performance.now() + QUIZ_MS;
let clockTimer = 0;
let roundTimer = 0;
let finished = false;

function row(p) {
  const li = document.createElement('li');
  li.className = 'row';
  li.innerHTML = '<span class="rank"></span><div><div class="name"></div><div class="bar"><i></i></div></div><span class="score"></span>';
  li.querySelector('.name').textContent = p.name;
  li.querySelector('.score').textContent = p.score;
  li.querySelector('.bar i').style.transform = 'scaleX(' + p.score / MAX + ')';
  rows.set(p.name, li);
  return li;
}

const fmt = (ms) => {
  const s = Math.ceil(ms / 1000);
  return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
};

function tickClock() {
  const left = Math.max(0, endAt - performance.now());
  clock.textContent = fmt(left);
  clock.classList.toggle('urgent', left < 10_000);
  if (left === 0) return finish();
  clockTimer = setTimeout(tickClock, (left % 1000) + 5);
}

const ease = (t) => 1 - (1 - t) ** 3;
function countTo(el, from, to, duration = 600) {
  cancelAnimationFrame(frames.get(el));
  if (reduce.matches) { el.textContent = to; return; }
  let start = null;
  const frame = (now) => {
    start ??= now;
    const t = Math.min(1, (now - start) / duration);
    el.textContent = Math.round(from + (to - from) * ease(t));
    if (t < 1) frames.set(el, requestAnimationFrame(frame));
  };
  frames.set(el, requestAnimationFrame(frame));
}

function flip(container, change) {
  const els = [...container.children];
  const first = new Map(els.map((el) => [el, el.getBoundingClientRect()]));
  els.forEach((el) => el.getAnimations().forEach((a) => a.cancel()));
  change();
  if (reduce.matches) return;
  for (const el of els) {
    const dy = first.get(el).top - el.getBoundingClientRect().top;
    if (dy) {
      el.animate([{ transform: 'translateY(' + dy + 'px)' }, { transform: 'none' }],
        { duration: 500, easing: 'cubic-bezier(.2,.8,.2,1)' });
    }
  }
}

function sortBoard() {
  flip(board, () => {
    PLAYERS.toSorted((a, b) => b.score - a.score).forEach((p, i) => {
      const li = rows.get(p.name);
      li.querySelector('.rank').textContent = i + 1;
      board.append(li);
    });
  });
}

function round() {
  for (let k = 0; k < 2; k++) {
    const p = PLAYERS[Math.floor(Math.random() * PLAYERS.length)];
    const before = p.score;
    p.score += 10 + Math.floor(Math.random() * 40);
    const li = rows.get(p.name);
    countTo(li.querySelector('.score'), before, p.score);
    li.querySelector('.bar i').style.transform = 'scaleX(' + Math.min(1, p.score / MAX) + ')';
  }
  sortBoard();
}

function finish() {
  finished = true;
  clearInterval(roundTimer);
  clearTimeout(clockTimer);
  clock.textContent = 'Finished';
  clock.classList.remove('urgent');
  const top = board.firstElementChild;
  top.classList.add('winner');
  top.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.04)' }, { transform: 'scale(1)' }],
    { duration: reduce.matches ? 0 : 600, iterations: 2 });
  console.log('Winner:', top.querySelector('.name').textContent);
}

document.addEventListener('visibilitychange', () => {
  if (finished) return;
  clearInterval(roundTimer);
  if (!document.hidden) roundTimer = setInterval(round, 2000);
  tickClock();                                // correct time the moment we are back
});

board.append(...PLAYERS.map(row));
sortBoard();
roundTimer = setInterval(round, 2000);
tickClock();
