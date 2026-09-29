import { signal, effect, computed } from './signals.js';

const KEY = 'ralfiz-signal-tasks';
const SEED = [
  { id: 1, title: 'Send quote for the Ralfiz Store redesign', done: false },
  { id: 2, title: 'Review pull request #42', done: true },
  { id: 3, title: 'Plan sprint demo', done: false },
];
function loadTasks() {
  try { return JSON.parse(localStorage.getItem(KEY)) ?? SEED; } catch { return SEED; }
}

// ---- state ----
const tasks = signal(loadTasks());
const filter = signal('all');
const visible = computed(() => tasks.get().filter((t) =>
  filter.get() === 'all' || (filter.get() === 'done') === t.done));
const remaining = computed(() => tasks.get().filter((t) => !t.done).length);

// ---- components ----
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

// ---- effects ----
const list = document.querySelector('#list');
effect(() => keyedList(list, visible.get()));
effect(() => { document.querySelector('#left').textContent = `${remaining.get()} left`; });
effect(() => {
  const current = filter.get();
  document.querySelectorAll('[data-f]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.f === current));
});
effect(() => localStorage.setItem(KEY, JSON.stringify(tasks.get())));

// ---- events: only set signals ----
document.querySelector('#add').addEventListener('submit', (ev) => {
  ev.preventDefault();
  const title = ev.target.elements.title.value.trim();
  if (title) tasks.set([...tasks.get(), { id: Date.now(), title, done: false }]);
  ev.target.reset();
});
list.addEventListener('change', (ev) => {
  const id = Number(ev.target.closest('li').dataset.key);
  tasks.set(tasks.get().map((t) => (t.id === id ? { ...t, done: ev.target.checked } : t)));
});
list.addEventListener('click', (ev) => {
  const del = ev.target.closest('.del');
  if (del) tasks.set(tasks.get().filter((t) => String(t.id) !== del.closest('li').dataset.key));
});
document.querySelector('.filters').addEventListener('click', (ev) => {
  if (ev.target.dataset.f) filter.set(ev.target.dataset.f);
});
document.querySelector('#clear').addEventListener('click', () => tasks.set(tasks.get().filter((t) => !t.done)));
