// Task Board: state → render, with filters in the URL hash and localStorage.
const STORAGE_KEY = 'ralfiz.taskboard.v1';
const FILTERS = {
  all: () => true,
  active: (task) => !task.done,
  done: (task) => task.done,
};

const DEMO_TASKS = [
  { id: 'd1', text: 'Send the Ralfiz Store pilot report', done: true },
  { id: 'd2', text: 'Fix GST rounding in invoices', done: false },
  { id: 'd3', text: 'Prepare the demo for Friday', done: false },
];

// ---------- state ----------
function loadTasks() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return DEMO_TASKS; // first visit
    const saved = JSON.parse(raw);
    return Array.isArray(saved) ? saved : [];
  } catch {
    return []; // corrupted data should never break the app
  }
}

const state = {
  tasks: loadTasks(),
  filter: 'all',
  editingId: null,
};

function filterFromHash() {
  const name = location.hash.replace('#/', '');
  return name in FILTERS ? name : 'all';
}

// The ONE place that changes state
function update(patch) {
  Object.assign(state, patch);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.tasks));
  } catch (err) {
    console.warn('Could not save tasks:', err.name);
  }
  render();
}

// ---------- rendering ----------
const $ = (selector) => document.querySelector(selector);

function taskItem(task) {
  const li = document.createElement('li');
  li.dataset.id = task.id;
  li.classList.toggle('done', task.done);

  const box = document.createElement('input');
  box.type = 'checkbox';
  box.checked = task.done;
  box.id = `task-${task.id}`;
  box.setAttribute('aria-label', `Done: ${task.text}`);

  let text;
  if (state.editingId === task.id) {
    text = document.createElement('input');
    text.className = 'edit';
    text.value = task.text;
    text.setAttribute('aria-label', 'Edit task');
  } else {
    text = document.createElement('span');
    text.className = 'text';
    text.textContent = task.text;
  }

  const del = document.createElement('button');
  del.className = 'del';
  del.type = 'button';
  del.textContent = '✕';
  del.setAttribute('aria-label', `Delete ${task.text}`);

  li.append(box, text, del);
  return li;
}

function render() {
  const focusedId = document.activeElement?.id;
  const visible = state.tasks.filter(FILTERS[state.filter]);
  $('#list').replaceChildren(...visible.map(taskItem));

  // derived values
  const left = state.tasks.filter(FILTERS.active).length;
  const done = state.tasks.length - left;
  $('#left').textContent = `${left} item${left === 1 ? '' : 's'} left`;
  $('#summary').textContent = `${done}/${state.tasks.length} done`;
  $('#empty').hidden = visible.length > 0;
  $('#clear').disabled = done === 0;
  for (const link of document.querySelectorAll('[data-filter]')) {
    if (link.dataset.filter === state.filter) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }

  const editor = $('.edit');
  if (editor) editor.focus();
  else if (focusedId) document.getElementById(focusedId)?.focus();
}

// ---------- events ----------
$('#add-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const input = event.target.elements.text;
  const text = input.value.trim();
  if (!text) return;
  const task = { id: String(Date.now()), text, done: false };
  update({ tasks: [task, ...state.tasks] });
  input.value = '';
});

const idOf = (el) => el.closest('li')?.dataset.id;

$('#list').addEventListener('change', (event) => {
  if (event.target.type !== 'checkbox') return;
  const id = idOf(event.target);
  update({ tasks: state.tasks.map((t) => (t.id === id ? { ...t, done: !t.done } : t)) });
});

$('#list').addEventListener('click', (event) => {
  if (!event.target.matches('.del')) return;
  const id = idOf(event.target);
  update({ tasks: state.tasks.filter((t) => t.id !== id) });
  $('#add-form input').focus(); // the focused button is gone
});

$('#list').addEventListener('dblclick', (event) => {
  if (event.target.matches('.text')) update({ editingId: idOf(event.target) });
});

function saveEdit(input) {
  const id = idOf(input);
  const text = input.value.trim();
  const tasks = text
    ? state.tasks.map((t) => (t.id === id ? { ...t, text } : t))
    : state.tasks.filter((t) => t.id !== id); // empty text deletes
  update({ tasks, editingId: null });
}

$('#list').addEventListener('keydown', (event) => {
  if (!event.target.matches('.edit')) return;
  if (event.key === 'Enter') saveEdit(event.target);
  if (event.key === 'Escape') update({ editingId: null });
});

$('#list').addEventListener('focusout', (event) => {
  if (event.target.matches('.edit') && state.editingId) saveEdit(event.target);
});

$('#clear').addEventListener('click', () => {
  update({ tasks: state.tasks.filter(FILTERS.active) });
});

addEventListener('hashchange', () => update({ filter: filterFromHash() }));

state.filter = filterFromHash();
render();
