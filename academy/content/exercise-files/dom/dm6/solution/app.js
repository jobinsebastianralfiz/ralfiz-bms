// Lab 2.2 - Propagation and event delegation (solution)
const list = document.querySelector('#list');
const filters = document.querySelector('#filters');
const leftEl = document.querySelector('#left');
const form = document.querySelector('#new');
const input = document.querySelector('#title');
const clearBtn = document.querySelector('#clear');

let tasks = [
  { id: 1, title: 'Review pull request #42', done: true },
  { id: 2, title: 'Fix cart total rounding', done: false },
  { id: 3, title: 'Write release notes for v2.3', done: false },
];
let filter = 'all';
let nextId = 4;
let editing = false;

function renderItem(task) {
  const li = document.createElement('li');
  li.className = task.done ? 'item done' : 'item';
  li.dataset.id = task.id;
  const box = document.createElement('input');
  box.type = 'checkbox';
  box.className = 'toggle';
  box.checked = task.done;
  box.setAttribute('aria-label', `Done: ${task.title}`);
  const text = document.createElement('span');
  text.className = 'text';
  text.textContent = task.title;
  const del = document.createElement('button');
  del.type = 'button';
  del.className = 'delete';
  del.textContent = '×';
  del.setAttribute('aria-label', `Delete ${task.title}`);
  li.append(box, text, del);
  return li;
}

function render() {
  editing = false;
  const visible = tasks.filter((t) =>
    filter === 'all' ? true : filter === 'done' ? t.done : !t.done);
  list.replaceChildren(...visible.map(renderItem));
  if (!visible.length) {
    const li = document.createElement('li');
    li.className = 'empty';
    li.textContent = 'Nothing here.';
    list.append(li);
  }
  const left = tasks.filter((t) => !t.done).length;
  leftEl.textContent = `${left} ${left === 1 ? 'task' : 'tasks'} left`;
  clearBtn.disabled = !tasks.some((t) => t.done);
}

const findTask = (el) => tasks.find((t) => t.id === Number(el.closest('li').dataset.id));

// TODO(1): add
form.addEventListener('submit', (event) => {
  event.preventDefault();
  const title = input.value.trim();
  if (!title) return;
  tasks.unshift({ id: nextId++, title, done: false });
  form.reset();
  render();
});

// TODO(2): delete (one listener for every row)
list.addEventListener('click', (event) => {
  const del = event.target.closest('.delete');
  if (!del || !list.contains(del)) return;
  const task = findTask(del);
  tasks = tasks.filter((t) => t !== task);
  render();
});

// TODO(3): toggle ('change' bubbles from the checkbox to the list)
list.addEventListener('change', (event) => {
  if (!event.target.matches('.toggle')) return;
  findTask(event.target).done = event.target.checked;
  render();
});

// TODO(4): inline editing
list.addEventListener('dblclick', (event) => {
  const text = event.target.closest('.text');
  if (!text || editing) return;
  const field = document.createElement('input');
  field.className = 'edit';
  field.value = text.textContent;
  field.setAttribute('aria-label', 'Edit task');
  text.replaceWith(field);
  editing = true;
  field.focus();
  field.select();
});

list.addEventListener('keydown', (event) => {
  if (!event.target.matches('.edit')) return;
  if (event.key === 'Enter') event.target.blur(); // focusout saves
  if (event.key === 'Escape') render();           // cancel: redraw old title
});

list.addEventListener('focusout', (event) => {
  if (!event.target.matches('.edit') || !editing) return;
  const task = findTask(event.target);
  task.title = event.target.value.trim() || task.title;
  render();
});

// TODO(5): filters
filters.addEventListener('click', (event) => {
  const btn = event.target.closest('button[data-filter]');
  if (!btn) return;
  filter = btn.dataset.filter;
  for (const b of filters.querySelectorAll('button')) {
    b.setAttribute('aria-pressed', String(b === btn));
  }
  render();
});

// TODO(6): clear completed
clearBtn.addEventListener('click', () => {
  tasks = tasks.filter((t) => !t.done);
  render();
});

render();
