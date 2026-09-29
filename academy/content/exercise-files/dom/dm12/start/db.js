// A tiny promise wrapper around IndexedDB for one object store: notes.
const DB_NAME = 'ralfiz-notes';
const DB_VERSION = 1;
const STORE = 'notes';

let dbPromise = null;

export function openDB() {
  // TODO(5): open DB_NAME with indexedDB.open(DB_NAME, DB_VERSION) once
  //   and cache the promise in dbPromise (??=). In onupgradeneeded create
  //   the object store STORE with { keyPath: 'id', autoIncrement: true }
  //   and an index 'byDate' on 'createdAt'. Resolve with request.result,
  //   reject with request.error.
  return dbPromise;
}

// Turn an IDBRequest into a promise
function done(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// TODO(6): write store(mode): await openDB(), start a transaction on STORE
//   with the mode ('readonly' or 'readwrite') and return its objectStore.

export async function addNote(note) {
  // TODO(7): add the note and return the new id (use done()).
  console.log('addNote not implemented yet', note, typeof done);
}

export async function getAllNotes() {
  // TODO(7): getAll() through the 'byDate' index, newest first.
  return [];
}

export async function deleteNote(id) {
  // TODO(7): delete by id.
  console.log('deleteNote not implemented yet', id);
}
