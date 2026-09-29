# Lab 4.2 - Ralfiz Notes (browser storage)

One small app, three kinds of storage, each chosen on purpose:

| Data | Storage | Why |
|---|---|---|
| Theme preference | `localStorage` | small, must survive restarts, shared by tabs |
| Unsaved draft | `sessionStorage` | belongs to this tab only, gone when it closes |
| Saved notes | IndexedDB (`db.js`) | structured records, can grow large, async |

The script is an ES module (`type="module"`), so it uses `import` and
top-level `await`.

## Run it

Modules and IndexedDB need a real server, not `file://`. Open `dom/dm12/start`
with VS Code **Live Server**, or run `npx serve start` and open the address it
prints. Compare with `solution/` when you finish.

## Tasks

In `start/app.js`:
1. `readPrefs()` parses safely and merges over defaults.
2. The theme button saves the preference.
3. A `storage` event listener keeps other tabs in sync.
4. The draft autosaves to `sessionStorage` (debounced) and is restored on reload.

In `start/db.js`:
5. `openDB()` opens the database once and creates the store and index in
   `onupgradeneeded`.
6. `store(mode)` returns an object store inside a transaction.
7. `addNote`, `getAllNotes` (newest first) and `deleteNote`.

Back in `start/app.js`:
8. `noteItem()` renders a note with `textContent` and a delete button.
9. Submitting saves to IndexedDB, clears the form and the draft.

## Acceptance criteria

- Switching to dark mode survives a reload. With the app open in **two tabs**,
  switching in one tab switches the other.
- Typing half a note and reloading restores it; opening a **new tab** does not.
- Saved notes survive closing the browser. DevTools → Application → IndexedDB →
  `ralfiz-notes` → `notes` shows them.
- Deleting a note removes it from the list and from IndexedDB.
- A note titled `<img src=x onerror=alert(1)>` shows as text; no alert appears.
- Nothing sensitive (passwords, tokens) is stored anywhere in this app.
