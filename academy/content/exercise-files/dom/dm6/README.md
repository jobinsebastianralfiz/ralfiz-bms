# Lab 2.2 - Ralfiz Tasks with event delegation

Build a to-do list where **no row has its own listener**. Everything is handled
by a few delegated listeners on stable containers:

| Listener | On | Handles |
|---|---|---|
| submit | the form | adding a task |
| click | the list | delete buttons |
| change | the list | checkboxes |
| dblclick, keydown, focusout | the list | inline editing |
| click | the filter bar | All / Active / Done |
| click | Clear completed | removing done tasks |

## Run it

Open the `start` folder in VS Code and use **Live Server**, or run
`npx serve` in that folder. You only edit `app.js`: rendering is already
written for you, and you add the listeners (TODO(1) to TODO(6)).

## Acceptance criteria

1. Adding "Buy milk" shows it at the top; the counter reads 3 tasks left.
2. Ticking a task strikes it through and lowers the counter.
3. The × button deletes exactly the task in its row.
4. Double-clicking a title turns it into a text box. Enter or clicking away saves;
   Escape cancels.
5. The filter buttons show All / Active / Done and mark the chosen one with aria-pressed.
6. Clear completed removes every done task.
7. In DevTools, Elements > Event Listeners on an <li> shows no click listener of its own.
