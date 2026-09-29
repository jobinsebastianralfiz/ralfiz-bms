const PLAYERS = [
  { name: 'Anu', score: 120 }, { name: 'Rahul', score: 110 }, { name: 'Fatima', score: 95 },
  { name: 'Joel', score: 90 }, { name: 'Meera', score: 70 }, { name: 'Arjun', score: 60 },
];
const MAX = 600;
const QUIZ_MS = 90_000;
const board = document.querySelector('#board');
const clock = document.querySelector('#clock');
const rows = new Map();
let endAt = performance.now() + QUIZ_MS;
let clockTimer = 0;
let roundTimer = 0;

// TODO(4): const reduce = matchMedia('(prefers-reduced-motion: reduce)');

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
  // TODO(1): compute the time left from endAt, show fmt(left), toggle the
  // 'urgent' class under 10 seconds, call finish() at 0, otherwise schedule
  // the next tick with setTimeout for just after the next whole second.
}

function countTo(el, from, to) {
  // TODO(2): requestAnimationFrame loop over 600ms with easing (and cancel
  // the previous loop for this element, e.g. store the id in el.dataset).
  el.textContent = to;
}

function flip(container, change) {
  // TODO(3): First (measure), change(), Last (measure), Invert + Play (animate)
  change();
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
  // TODO(5): clear both timers, show 'Finished', add .winner to the top row
  // and pulse it with element.animate().
}

// TODO(6): pause/resume rounds on visibilitychange

board.append(...PLAYERS.map(row));
sortBoard();
roundTimer = setInterval(round, 2000);
tickClock();
