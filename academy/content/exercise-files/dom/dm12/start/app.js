// Ralfiz Notes: localStorage for preferences, sessionStorage for the draft,
// IndexedDB for the notes themselves.
import { addNote, getAllNotes, deleteNote } from './db.js';

const $ = (selector) => document.querySelector(selector);
const PREFS_KEY = 'notes:prefs:v1';
const DRAFT_KEY = 'notes:draft:v1';
const form = $('#editor');

// ---------- preferences (localStorage, shared by all tabs) ----------
function readPrefs() {
  // TODO(1): parse PREFS_KEY from localStorage inside try/catch and merge
  //   it over the default { theme: 'light' }.
  return { theme: 'light' };
}

function applyPrefs(prefs) {
  const dark = prefs.theme === 'dark';
  document.documentElement.classList.toggle('dark', dark);
  $('#theme').setAttribute('aria-pressed', String(dark));
  $('#theme').textContent = dark ? '☀️ Light mode' : '🌙 Dark mode';
}

$('#theme').addEventListener('click', () => {
  const prefs = readPrefs();
  prefs.theme = prefs.theme === 'dark' ? 'light' : 'dark';
  // TODO(2): save prefs as JSON under PREFS_KEY.
  applyPrefs(prefs);
});

// TODO(3): listen for the window 'storage' event. When event.key is
//   PREFS_KEY, call applyPrefs(readPrefs()) so other tabs follow along.

// ---------- draft (sessionStorage, this tab only) ----------
// TODO(4): on form input, wait 400 ms (debounce) and save
//   Object.fromEntries(new FormData(form)) to sessionStorage under DRAFT_KEY.
//   Write restoreDraft() so a reload puts the draft back in the form.
function restoreDraft() {}

// ---------- notes (IndexedDB) ----------
function noteItem(note) {
  // TODO(8): build <li><div><h3/><p/><time/></div><button class="del">✕</button></li>
  //   with textContent. The delete button awaits deleteNote(note.id) and
  //   then renderNotes().
  const li = document.createElement('li');
  li.textContent = note.title;
  return li;
}

async function renderNotes() {
  const notes = await getAllNotes();
  $('#notes').replaceChildren(...notes.map(noteItem));
  $('#empty').hidden = notes.length > 0;
  $('#count').textContent = notes.length ? `(${notes.length})` : '';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const { title, body } = Object.fromEntries(new FormData(form));
  // TODO(9): await addNote({ title, body, createdAt: Date.now() }), reset the
  //   form, remove the draft from sessionStorage and re-render the notes.
  console.log('submit', title, body, typeof addNote, typeof deleteNote);
});

applyPrefs(readPrefs());
restoreDraft();
await renderNotes();
