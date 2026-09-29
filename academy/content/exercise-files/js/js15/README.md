# Lab 3.4 - Store catalogue toolkit

Build four iteration tools for the Ralfiz Store.

## Run it

    cd javascript/js15/start
    node index.js

Node.js 22 or newer (iterator helpers such as .take() and .toArray()
are built in).

## Tasks (TODO markers in start/index.js)

1. TODO(1): invoiceNumbers(prefix, start): an infinite generator that
   yields strings like INV-2026-0041 (number padded to 4 digits).
2. TODO(2): make Catalogue iterable with a *[Symbol.iterator]() that yields
   only products with stock > 0.
3. TODO(3): add *byCategory(name) to Catalogue.
4. TODO(4): chunk(iterable, size): yield arrays of size items (last may be shorter).
5. TODO(5): a lazy query with iterator helpers: the first 3 in-stock products
   under 500 with rating >= 4.
6. TODO(6): add a Symbol.toStringTag getter that returns 'Catalogue'.

## Acceptance criteria

- The first three invoice numbers are INV-2026-0041, INV-2026-0042, INV-2026-0043.
- In stock: 8 of 10 products (Desk lamp and Scissors are sold out).
- Stationery: Notebook, Gel pen, Sticky notes, Planner.
- The chunked list prints 3 rows: 3 + 3 + 2 products.
- The lazy query prints Notebook, Gel pen, Steel bottle.
- String(catalogue) prints [object Catalogue].
