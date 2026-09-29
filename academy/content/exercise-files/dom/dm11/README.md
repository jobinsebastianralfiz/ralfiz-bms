# Lab 4.1 - Ralfiz Store product browser

Load products from DummyJSON into a responsive grid with every UI state a
real shop needs: loading skeletons, errors with retry, an empty result and
success. Add **Load more** pagination, a **debounced search** that cancels
stale requests with `AbortController`, and a `Map` cache.

API: `https://dummyjson.com/products?limit=12&skip=0&select=title,brand,price,rating,thumbnail`
and `https://dummyjson.com/products/search?q=phone`.

## Run it

Open `dom/dm11/start` with VS Code **Live Server** or run `npx serve start`,
then open the address it prints. The finished version is in `solution/`.

## Tasks (TODOs in start/app.js)

1. `pageUrl()` builds URLs with `URLSearchParams`.
2. `fetchPage()` checks the cache, fetches with a signal, throws on `!res.ok`.
3. `productCard()` fills the cloned `<template>` safely with `textContent`.
4. `renderStatus()` shows the right status text, error box and Load more button.
5. `load()` aborts the previous request.
6. `load()` ignores `AbortError` and shows other errors.
7. The search box is debounced by 300 ms.
8. Load more and Try again buttons work.

## Acceptance criteria

- On load you see skeleton cards, then 12 products and “Showing 12 of 194”
  (the live API currently has 194 products; the number may change).
- **Load more** adds 12 more; it disappears when everything is loaded.
- Typing `phone` quickly sends **one** request (check the Network panel);
  typing fast while a request is pending shows it as *(canceled)*.
- Clearing the search and typing `phone` again loads instantly from the cache.
- Searching `zzzz` shows “No products match”.
- With DevTools → Network → **Offline**, reloading shows the error box, and
  **Try again** works once you are back online.
