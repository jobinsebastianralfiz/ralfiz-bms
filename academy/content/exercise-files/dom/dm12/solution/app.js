// Ralfiz Notes: localStorage for preferences, sessionStorage for the draft,
// IndexedDB for the notes themselves.
import { addNote, getAllNotes, deleteNote } from './db.js';

const $ = (selector) => document.querySelector(selector);
const PREFS_KEY = 'notes:prefs:v1';
const DRAFT_KEY = 'notes:draft:v1';
const form = $('#editor');

// ---------- preferences (localStorage, shared by all tabs) ----------
function readPrefs() {
  try {
    return { theme: 'light', ...JSON.parse(localStorage.getItem(PREFS_KEY)) };
  } catch {
    return { theme: 'light' };
  }
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
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  applyPrefs(prefs);
});

// Fires in OTHER tabs of the same origin when localStorage changes
addEventListener('storage', (event) => {
  if (event.key === PREFS_KEY) applyPrefs(readPrefs());
});

// ---------- draft (sessionStorage, this tab only) ----------
let draftTimer;
form.addEventListener('input', () => {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(() => {
    const draft = Object.fromEntries(new FormData(form));
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    $('#draft-status').textContent = 'Draft saved in this tab';
  }, 400);
});

function restoreDraft() {
  try {
    const draft = JSON.parse(sessionStorage.getItem(DRAFT_KEY));
    if (!draft) return;
    form.elements.title.value = draft.title ?? '';
    form.elements.body.value = draft.body ?? '';
    $('#draft-status').textContent = 'Draft restored';
  } catch {
    sessionStorage.removeItem(DRAFT_KEY);
  }
}

// ---------- notes (IndexedDB) ----------
const dateFormat = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' });

function noteItem(note) {
  const li = document.createElement('li');
  const box = document.createElement('div');
  const h3 = document.createElement('h3');
  h3.textContent = note.title;
  const p = document.createElement('p');
  p.textContent = note.body;
  const time = document.createElement('time');
  time.dateTime = new Date(note.createdAt).toISOString();
  time.textContent = dateFormat.format(note.createdAt);
  box.append(h3, p, time);
  const del = document.createElement('button');
  del.className = 'del';
  del.type = 'button';
  del.textContent = '✕';
  del.setAttribute('aria-label', `Delete ${note.title}`);
  del.addEventListener('click', async () => {
    await deleteNote(note.id);
    await renderNotes();
  });
  li.append(box, del);
  return li;
}

async function renderNotes() {
  try {
    const notes = await getAllNotes();
    $('#notes').replaceChildren(...notes.map(noteItem));
    $('#empty').hidden = notes.length > 0;
    $('#count').textContent = notes.length ? `(${notes.length})` : '';
  } catch (err) {
    $('#empty').textContent = `Could not open the notes database (${err.name}).`;
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const { title, body } = Object.fromEntries(new FormData(form));
  await addNote({ title: title.trim(), body: body.trim(), createdAt: Date.now() });
  form.reset();
  clearTimeout(draftTimer);
  sessionStorage.removeItem(DRAFT_KEY);
  $('#draft-status').textContent = 'Saved to IndexedDB';
  await renderNotes();
});

applyPrefs(readPrefs());
restoreDraft();
await renderNotes();
