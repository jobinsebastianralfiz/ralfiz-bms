// Lab 1.3 - Notification centre (solution). Loaded as a module: top-level await works.
const list = document.querySelector('#list');
const template = document.querySelector('#note-tpl');
const badge = document.querySelector('#unread');
const empty = document.querySelector('#empty');
const message = document.querySelector('#message');

async function loadNotifications() {
  const response = await fetch('notifications.json');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function createNote(note) {
  const li = template.content.firstElementChild.cloneNode(true);
  li.querySelector('.icon').textContent = note.icon;
  li.querySelector('.text').textContent = note.text;   // safe: never parsed as HTML
  li.querySelector('.time').textContent = note.time;
  li.classList.toggle('unread', Boolean(note.unread));
  if (note.id) li.dataset.id = note.id;

  li.querySelector('.dismiss').addEventListener('click', () => {
    li.remove();
    updateCounts();
  });
  li.addEventListener('click', (event) => {
    if (event.target.closest('.dismiss')) return;
    li.classList.remove('unread');
    updateCounts();
  });
  return li;
}

function render(notes) {
  const fragment = document.createDocumentFragment();
  for (const note of notes) fragment.append(createNote(note));
  list.replaceChildren(fragment);          // one insertion for the whole list
  updateCounts();
}

// Derive the counts from the DOM so they can never drift out of sync.
function updateCounts() {
  const unread = list.querySelectorAll('.note.unread').length;
  badge.textContent = unread;
  badge.hidden = unread === 0;
  const isEmpty = list.children.length === 0;
  list.hidden = isEmpty;
  empty.hidden = !isEmpty;
  document.title = unread ? `(${unread}) Notifications · Ralfiz Academy` : 'Notifications · Ralfiz Academy';
}

let data = { notifications: [], incoming: [] };
try {
  data = await loadNotifications();
  message.hidden = true;
  render(data.notifications);
  console.log(`Rendered ${list.children.length} notifications`);
} catch (err) {
  message.textContent = `Could not load notifications (${err.message}).`;
  message.classList.add('error');
}

let next = 0;
document.querySelector('#new').addEventListener('click', () => {
  if (data.incoming.length === 0) return;
  const note = createNote({ ...data.incoming[next % data.incoming.length], unread: true });
  next += 1;
  note.classList.add('enter');
  list.prepend(note);
  updateCounts();
});

document.querySelector('#read-all').addEventListener('click', () => {
  list.querySelectorAll('.note.unread').forEach((li) => li.classList.remove('unread'));
  updateCounts();
});
