import { signal, effect, computed, ready } from './signals.js';

if (!ready) console.info('signals.js is not finished yet: see TODO(1) and TODO(2).');
const KEY = 'ralfiz-signal-tasks';
const SEED = [
  { id: 1, title: 'Send quote for the Ralfiz Store redesign', done: false },
  { id: 2, title: 'Review pull request #42', done: true },
  { id: 3, title: 'Plan sprint demo', done: false },
];

// TODO(3): tasks = signal(saved tasks ?? SEED); filter = signal('all');
// visible = computed(...); remaining = computed(...)

function TaskItem() {
  const li = document.createElement('li');
  li.innerHTML = '<label><input type="checkbox"><span></span></label><button class="del" type="button">✕</button>';
  return li;
}
function patchTaskItem(li, task) {
  li.dataset.key = task.id;
  li.classList.toggle('done', task.done);
  li.querySelector('input').checked = task.done;
  li.querySelector('span').textContent = task.title;
  li.querySelector('.del').setAttribute('aria-label', `Delete ${task.title}`);
}
function keyedList(parent, items) {
  const old = new Map([...parent.querySelectorAll('li[data-key]')].map((n) => [n.dataset.key, n]));
  let created = 0;
  const rows = items.map((task) => {
    const row = old.get(String(task.id)) ?? (created++, TaskItem());
    patchTaskItem(row, task);
    return row;
  });
  if (!rows.length) rows.push(Object.assign(document.createElement('li'), { className: 'empty', textContent: 'Nothing here.' }));
  parent.replaceChildren(...rows);
  console.log(`render: ${created} created, ${items.length - created} reused`);
}

const list = document.querySelector('#list');
keyedList(list, SEED); // TODO(4): replace with effect(() => keyedList(list, visible.get()))
// TODO(4): effects for #left ("2 left") and aria-pressed on [data-f] buttons.
// TODO(5): effect that saves tasks to localStorage.
// TODO(5): submit, change, click (.del), filter and #clear handlers that only call set().
