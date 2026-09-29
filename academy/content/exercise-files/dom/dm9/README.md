# Lab 3.2 - Ralfiz Academy course page (UI components)

Build the behaviour of four components on one page: a modal enrol form
with `<dialog>`, accessible tabs, a custom accordion and toast notifications.
The HTML and CSS are finished; you only write `app.js`.

## Run it

Open the `start` folder in VS Code and use **Live Server**
(right-click `index.html` → Open with Live Server), or run:

```bash
npx serve start
```

Then open the address it prints. Compare with `solution/` when you are done.

## Tasks (TODOs in start/app.js)

1. `toast()` builds a toast with `createElement` and `textContent`, adds it to
   `#toasts` and removes it after 4 seconds or when ✕ is clicked.
2. Hovering a toast pauses its timer; leaving resumes it.
3. `select()` in `initTabs` updates `aria-selected`, `tabIndex` and `hidden`.
4. Clicking a tab selects it; ← → wrap around, Home and End jump.
5. The FAQ accordion toggles `aria-expanded` and the panel's `hidden`.
6. "Reserve a seat" opens the dialog with `showModal()`; Cancel, Esc and a
   backdrop click close it.
7. On close, focus returns to the button, and a successful reservation shows
   a toast built from `FormData`.

## Acceptance criteria

- Keyboard only: Tab reaches the tab list once; arrow keys move between tabs
  and the matching panel shows.
- The dialog traps focus, closes with Esc, and focus returns to "Reserve a seat".
- Submitting with an empty name shows the browser's validation message and the
  dialog stays open.
- A valid submit shows "Seat reserved for …" in a toast that disappears after
  4 seconds (hover keeps it on screen).
- No errors in the DevTools console.
