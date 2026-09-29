// Task Board: state → render, with filters in the URL hash and localStorage.
const STORAGE_KEY = 'ralfiz.taskboard.v1';
const FILTERS = {
  all: () => true,
  active: (task) => !task.done,
  done: (task) => task.done,
};

// ---------- state ----------
function loadTasks() {
  // TODO(1): read STORAGE_KEY from localStorage and JSON.parse it.
  //   Return a few demo tasks when nothing is saved yet (getItem gives null),
  //   the array when it is valid, and [] when the value is not an array
  //   or JSON.parse throws (use try/catch).
  return [];
}

const state = {
  tasks: loadTasks(),
  filter: 'all',
  editingId: null,
};

function filterFromHash() {
  // TODO(2): turn '#/active' into 'active'. Return 'all' for anything
  //   that is not a key of FILTERS.
  return 'all';
}

// The ONE place that changes state
function update(patch) {
  Object.assign(state, patch);
  // TODO(3): save state.tasks as JSON (wrap setItem in try/catch).
  render();
}

// ---------- rendering ----------
const $ = (selector) => document.querySelector(selector);

function taskItem(task) {
  const li = document.createElement('li');
  li.dataset.id = task.id;
  // TODO(4): build <input type="checkbox" id="task-ID">, a <span class="text">
  //   (or <input class="edit"> when state.editingId === task.id) and a
  //   <button class="del">✕</button>. Use textContent for the task text,
  //   add the 'done' class and aria-labels, then append them to li.
  li.textContent = task.text;
  return li;
}

function render() {
  const visible = state.tasks.filter(FILTERS[state.filter]);
  $('#list').replaceChildren(...visible.map(taskItem));
  // TODO(5): derived values. Update #left ("2 items left"), #summary
  //   ("1/3 done"), #empty.hidden, #clear.disabled and aria-current="page"
  //   on the active filter link.
  // TODO(6): restore focus. Remember document.activeElement.id before
  //   re-rendering and focus the element with that id afterwards;
  //   focus .edit if a task is being edited.
}

// ---------- events ----------
$('#add-form').addEventListener('submit', (event) => {
  event.preventDefault();
  // TODO(7): trim the text, ignore empty input, then
  //   update({ tasks: [newTask, ...state.tasks] }) and clear the input.
});

// TODO(8): delegated listeners on #list:
//   change   → toggle done for the checkbox's task
//   click    → .del removes the task (then focus the add input)
//   dblclick → .text sets editingId
//   keydown  → Enter saves the .edit value, Escape cancels
// Then: #clear removes done tasks, and hashchange updates the filter.

state.filter = filterFromHash();
render();
console.log('Task Board starter loaded with', state.tasks.length, 'tasks');
