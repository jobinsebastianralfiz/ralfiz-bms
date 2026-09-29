// A tiny promise wrapper around IndexedDB for one object store: notes.
const DB_NAME = 'ralfiz-notes';
const DB_VERSION = 1;
const STORE = 'notes';

let dbPromise = null;

// Open once and reuse the connection
export function openDB() {
  dbPromise ??= new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    // Runs on first open and whenever DB_VERSION goes up: create the schema here
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true });
        store.createIndex('byDate', 'createdAt');
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  return dbPromise;
}

// Turn an IDBRequest into a promise
function done(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function store(mode) {
  const db = await openDB();
  return db.transaction(STORE, mode).objectStore(STORE);
}

export async function addNote(note) {
  return done((await store('readwrite')).add(note)); // resolves to the new id
}

export async function getAllNotes() {
  const notes = await done((await store('readonly')).index('byDate').getAll());
  return notes.reverse(); // newest first
}

export async function deleteNote(id) {
  return done((await store('readwrite')).delete(id));
}
