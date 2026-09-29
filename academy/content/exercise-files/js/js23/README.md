# js23 · Split an invoice script into ES modules

`start/index.js` is an older-style CommonJS script: money helpers, a `Cart`
class and the program are all in one file. Turn it into ES modules.

## Run

```bash
cd start
node index.js           # prints the invoice
node index.js --save    # also writes invoice.txt
```

Node 22 or newer.

## Tasks

Follow `TODO(1)` to `TODO(8)` in `start/index.js`:

1. Create `start/cart.js`. Move `GST_RATE` and `formatINR` into it as named
   exports and `Cart` as the default export.
2. Add `start/package.json` containing `{ "type": "module" }`.
3. In `index.js`, import from `./cart.js` (with the `.js` extension) and
   delete `'use strict'`, `require` and `module.exports`.
4. Load `node:fs/promises` with `await import()` only inside the `--save`
   branch, and build the path with `new URL('./invoice.txt', import.meta.url)`.
5. Replace `main().catch()` with top-level `await`.

## Acceptance criteria

- `node index.js` prints the same invoice as before, ending with
  `Total ... ₹4,715.28` and `GST 18%: ₹719.28`.
- The last line reads `Loaded as an ES module: index.js`.
- `node index.js --save` writes `invoice.txt` next to `index.js`.
- There is no `require`, `module.exports` or `__dirname` left anywhere.

The finished version is in `solution/`.
