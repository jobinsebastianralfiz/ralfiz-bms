# dm22 · Project: Ralfiz Store product search

Build a product browser on the DummyJSON API (https://dummyjson.com/products).

## Run it
This app uses real URLs (?q=…&page=…) and history.pushState, so serve it:

    npx serve start        # or open the folder with VS Code Live Server

The `solution` folder is the finished app.

## Tasks (TODOs in start/app.js)
1. TODO(1) readUrl() / writeUrl(): q, cat, sort and page round-trip through location.search.
2. TODO(2) apiUrl(): /products, /products/search or /products/category/{slug} with limit, skip, select, sortBy, order.
3. TODO(3) load(): abort the previous request, skeletons, Map cache, response.ok, ignore AbortError.
4. TODO(4) render(): success, empty and error states; status text; page info; Prev/Next disabled at the ends.
5. TODO(5) events: 300 ms debounce on search; chips, sort, paging and popstate through update().
6. TODO(6) detail dialog (showModal + /products/{id}) and a cart saved in localStorage.

## Acceptance criteria
- Typing "phone" quickly sends one request; in DevTools (Slow 4G) earlier requests show as canceled.
- The address bar shows ?q=phone; reloading or sharing that URL shows the same results.
- Clicking a category, then Back, returns to the previous view.
- Searching "zzzz" shows the empty state; going offline and pressing Retry shows the error state.
- Opening a product shows its description in a dialog; Escape closes it and focus returns to the card.
- The cart count and total survive a reload.
- Every product image has alt, width and height.
