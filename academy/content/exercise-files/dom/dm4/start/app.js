// Lab 1.3 - Notification centre (starter). Loaded as a module: top-level await works.
const list = document.querySelector('#list');
const template = document.querySelector('#note-tpl');
const badge = document.querySelector('#unread');
const empty = document.querySelector('#empty');
const message = document.querySelector('#message');

// Loading data is done for you: note the !response.ok check.
async function loadNotifications() {
  const response = await fetch('notifications.json');
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function createNote(note) {
  // TODO(1): clone template.content.firstElementChild with cloneNode(true).
  // Fill .icon, .text and .time with textContent, and toggle the 'unread'
  // class with note.unread. Return the li.
  // TODO(3): add a click listener to the li's .dismiss button that calls
  // li.remove() and then updateCounts().
  const li = document.createElement('li');
  li.textContent = note.text;
  return li;
}

function render(notes) {
  // TODO(2): create a DocumentFragment, append createNote(n) for every note,
  // then insert everything with list.replaceChildren(fragment).
  console.log('render() received', notes.length, 'notes');
  updateCounts();
}

function updateCounts() {
  // TODO(4): count list.querySelectorAll('.note.unread'), write it into the
  // badge, hide the badge when it is 0, hide the list and show #empty when
  // list.children.length is 0.
}

let data = { notifications: [], incoming: [] };
try {
  data = await loadNotifications();
  message.hidden = true;
  list.hidden = false;
  render(data.notifications);
} catch (err) {
  message.textContent = `Could not load notifications (${err.message}).`;
  message.classList.add('error');
}

let next = 0;
document.querySelector('#new').addEventListener('click', () => {
  // TODO(5): take data.incoming[next % data.incoming.length], create a note
  // with unread: true, add the 'enter' class, list.prepend() it, then
  // updateCounts(). Increase next.
});

document.querySelector('#read-all').addEventListener('click', () => {
  // TODO(6): remove 'unread' from every .note.unread, then updateCounts().
});
