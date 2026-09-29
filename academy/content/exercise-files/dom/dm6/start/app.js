// Lab 2.2 - Propagation and event delegation
// Rule for this lab: never call addEventListener on a row or anything inside it.

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

// Helper: find the task for any element inside a row
const findTask = (el) => tasks.find((t) => t.id === Number(el.closest('li').dataset.id));

// TODO(1): 'submit' on the form: preventDefault, add a task at the TOP
//          (unshift) with nextId++, reset the form and render()

// TODO(2): ONE 'click' listener on the list for delete buttons.
//          Use event.target.closest('.delete'); return if nothing matched.

// TODO(3): ONE 'change' listener on the list for checkboxes.
//          Use event.target.matches('.toggle'), update task.done, render()

// TODO(4): inline editing, all delegated on the list:
//   - 'dblclick' on a .text: replace it with <input class="edit">, focus, select,
//     set editing = true
//   - 'keydown' in .edit: Enter -> blur(); Escape -> render() (cancel)
//   - 'focusout' from .edit: save the trimmed value (keep the old one if empty)

// TODO(5): ONE 'click' listener on #filters: closest('button[data-filter]'),
//          set filter, update aria-pressed on all three buttons, render()

// TODO(6): Clear completed removes every done task and renders

render();
