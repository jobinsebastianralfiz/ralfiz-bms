# Lab 5.2 - An accessible Ralfiz Store header and cart

The page in `start/` looks finished, but a keyboard or screen reader user cannot use it.
Fix it with semantic HTML first and a little ARIA.

## Run it

Open `dom/dm19/start` with VS Code **Live Server**, or run `npx serve` in that folder.

## Tasks

- TODO(1) `index.html`: real buttons, logo alt text, a label for search, a skip link.
- TODO(2) `style.css`: remove `outline: none`; add `:focus-visible` and `.sr-only`.
- TODO(3) `app.js`: Categories disclosure with `aria-expanded`, Escape and focus-out closing.
- TODO(4) A `role="status"` live region that announces cart changes.
- TODO(5) Accessible names: "Add Desk Lamp to cart", "Remove Desk Lamp".
- TODO(6) Focus after removing a cart line: next line, else the cart heading.

## Test it

1. Keyboard only: Tab, Shift+Tab, Enter, Space, Escape.
2. A screen reader: NVDA (Windows), VoiceOver (Cmd+F5 on macOS) or TalkBack (Android).
3. Chrome DevTools > Lighthouse > Accessibility, and the axe DevTools extension.

## Acceptance criteria

- The first Tab shows a "Skip to content" link.
- Every control is reachable and shows a clear focus ring.
- Categories announces "collapsed"/"expanded"; Escape closes it and focus returns to it.
- Adding an item announces e.g. "Desk Lamp added. 1 item, ₹1,499."
- Removing a line never leaves focus on the page body.
- Lighthouse Accessibility reports no failed audits on the solution.
