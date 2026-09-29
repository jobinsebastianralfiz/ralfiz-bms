# Lab 2.1 - Ralfiz Academy post card

Build an interactive community post using only DOM events:

- a like button that toggles (with aria-pressed) and a double-click-to-like gesture
- a comment box with a live character counter (200 characters, emoji count as 1)
- Ctrl+Enter / Cmd+Enter to post a comment
- a one-time tip banner ({ once: true })
- a Close discussion button that removes every listener with one AbortController

## Run it

Open the `start` folder in VS Code and use the **Live Server** extension,
or run `npx serve` inside the folder and open the address it prints.
All the HTML and CSS is ready. You only edit `app.js` (TODO(1) to TODO(7)).

## Acceptance criteria

1. Clicking the heart toggles it pink, the count goes 41 -> 42 -> 41, and the
   console logs the target and currentTarget tag names.
2. Double-clicking the post text likes the post (never un-likes) and shows the big heart.
3. Typing updates "N left" on every keystroke; at 20 left the counter turns amber,
   over 200 it turns red and the Post button is disabled. An emoji counts as one.
4. Posting adds the comment at the bottom of the list, as plain text
   (try typing <b>hi</b>: you must see the tags, not bold text).
5. Ctrl+Enter (Cmd+Enter on a Mac) posts without adding a new line.
6. Got it hides the tip. Close discussion stops the like button, the counter and posting.

## Think about it

- Why does the submit listener go on the form and not on the Post button?
- What would happen if you called form.submit() instead of form.requestSubmit()?
