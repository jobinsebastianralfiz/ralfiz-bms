# Lab 0.1 - Profile card

Build your first live page: a Ralfiz Academy mentor profile card, filled from a
JavaScript object, with a working Follow button. On the way you see *when* a
script runs and why `defer` matters.

## Run it

1. Open the `dom/dm1` folder in VS Code.
2. Right-click `start/index.html` and choose **Open with Live Server**
   (extension: "Live Server"). Or, in a terminal inside `dom/dm1`, run
   `npx serve` and open the printed URL, then `/start/`.
3. Open DevTools with F12 (Cmd+Option+I on a Mac) and keep the **Console** open.

## Tasks

All TODOs are in `start/index.html` and `start/app.js`.

1. **TODO(1)** The console says `card found? false`. Add `defer` to the
   `<script>` tag in the head. Reload: it says `true`. Why?
2. **TODO(2)** Log `document.readyState` at the top of `app.js`, then inside a
   `DOMContentLoaded` listener and a `load` listener.
3. **TODO(3)** Fill the card from the `profile` object with `textContent`:
   name, role, initials and the three stats. Show followers as `4.8k`.
4. **TODO(4)** For each skill, create a `<span>` and append it to `.tags`.
5. **TODO(5)** Make **Follow** a toggle: text Follow/Following,
   `aria-pressed` true/false, follower count up/down by one.

## Acceptance criteria

- The console shows `card found? true` and the readyState sequence
  `interactive`, `interactive`, `complete` (top of file with defer, DOMContentLoaded, load).
- The card shows Anjali Menon, the role, `AM`, 12 / 4.8k / 4.9 and four skill tags.
- Clicking Follow changes the text to Following and logs `followers: 4801`;
  clicking again shows Follow and logs `followers: 4800`.
- No errors in the console.

## Think about it

- Why does the readyState at the top of a deferred script say `interactive`,
  while in the playground it said `loading`?
- In the **Network** panel, which file starts downloading first, `style.css`
  or `app.js`? Does `defer` delay the download or only the execution?
- In the **Elements** panel, find the spans you created. Are they in
  `index.html`? Where do they live?
