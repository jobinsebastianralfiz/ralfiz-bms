# Lab 3.3 - Task Board (state-driven rendering)

Build a to-do board where **every change goes through one `update()`
function**, the list is drawn by one `render()` function, and anything that
can be calculated (counts, the visible list) is derived instead of stored.

## Run it

Open `dom/dm10/start` with VS Code **Live Server**, or run `npx serve start`
and open the address it prints. The solution is in `solution/`.

## Tasks (TODOs in start/app.js)

1. `loadTasks()` reads and parses `localStorage` safely.
2. `filterFromHash()` maps `#/active` → `active` (default `all`).
3. `update()` saves `state.tasks` after every change.
4. `taskItem()` builds a row with a checkbox, the text and a delete button.
5. `render()` updates the counters, empty message, Clear button and the
   current filter link.
6. `render()` restores keyboard focus after replacing the list.
7. The form adds new tasks at the top.
8. Delegated listeners: toggle, delete, double-click to edit (Enter saves,
   Esc cancels, empty text deletes), Clear completed, and `hashchange`.

## Acceptance criteria

- On a first visit the three demo tasks show **2 items left** and **1/3 done**;
  adding one task changes that to **3 items left** and **1/4 done**.
- Clicking **Active** changes the URL to `#/active` and hides done tasks;
  the browser Back button returns to the previous filter.
- **Clear completed** removes only done tasks and is disabled when there are none.
- Reloading the page keeps your tasks (but the filter comes from the URL).
- Toggling a checkbox with the Space key keeps focus on that checkbox.
- Typing `<b>hi</b>` as a task shows the tags as text, not bold.
