# Lab 1.3 - Notification centre

Build the Ralfiz Academy notification centre: load notifications from a JSON
file, render them from a `<template>`, add new ones at the top, dismiss them,
mark them read and keep an unread badge in sync.

## Run it

`fetch` needs a web server (it does not work from `file://`). Open `dom/dm4` in
VS Code and start **Live Server** on `start/index.html`, or run `npx serve`
inside `dom/dm4` and open `/start/`. Keep DevTools open.

`app.js` is loaded with `type="module"`, so it is deferred automatically and
can use top-level `await`.

## Tasks (in `start/app.js`)

1. **TODO(1)** `createNote`: clone `template.content.firstElementChild` with
   `cloneNode(true)` and fill it with `textContent`. Toggle `unread`.
2. **TODO(2)** `render`: build every note into a `DocumentFragment`, then
   insert it with `list.replaceChildren(fragment)`.
3. **TODO(3)** The ✕ button removes its note with `li.remove()`.
4. **TODO(4)** `updateCounts`: badge = number of `.note.unread`; hide the badge
   at 0; show `#empty` and hide the list when there are no notes.
5. **TODO(5)** **+ New** prepends the next incoming notification (unread,
   with the `enter` class for the animation).
6. **TODO(6)** **Mark all read** removes `unread` from every note.

## Acceptance criteria

- On load, five notifications appear and the badge shows **3**.
- **+ New** adds a notification at the top with a slide-in and the badge
  goes to **4**.
- Clicking a notification marks it read (the badge drops by one); ✕ removes it.
- After dismissing every notification, "You're all caught up" is shown and the
  badge is hidden.
- Rename `notifications.json` temporarily: the page shows a red
  "Could not load notifications (HTTP 404)" message instead of crashing.

## Think about it

- Why does `updateCounts` count `.note.unread` in the DOM instead of keeping a
  separate `let unread = 3` variable?
- What would break if the template contained `<li id="note">`?
- Replace `list.prepend(note)` with `list.innerHTML += ...`. What happens to
  the ✕ buttons of the older notes? Why?
