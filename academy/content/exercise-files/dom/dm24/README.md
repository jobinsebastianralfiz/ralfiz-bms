# dm24 · A signals library and a Task Board on top of it

Write a 25-line reactive core (signal, effect, computed), then build the Task Board with it.
Finally compare it with the React version in reference/TaskBoard.jsx.

## Run it
The app uses ES modules, so serve the folder:

    npx serve start        # or VS Code Live Server

## Tasks
1. TODO(1) signals.js: signal(value) with get() that tracks the running effect and set() that skips equal values.
2. TODO(2) signals.js: effect(fn) and computed(fn).
3. TODO(3) app.js: tasks and filter signals; visible and remaining computed values.
4. TODO(4) app.js: an effect that renders with keyedList(); an effect for the counter and the filter buttons.
5. TODO(5) app.js: an effect that saves to localStorage; events that only call set() with new arrays.
6. Read reference/TaskBoard.jsx and match each React line with your vanilla line.

## Acceptance criteria
- Ticking a task updates the "N left" pill without re-creating other rows (console: "0 created").
- Switching to Done shows only completed tasks and highlights the Done button.
- Clear completed removes done tasks; reloading keeps the list.
- Toggling the filter never writes to localStorage (add a console.log to the save effect to prove it).

## Think about it
- Which effects run when you type a new task and press Enter? Why not the filter-button effect?
- In React, which line replaces your keyedList() call?
