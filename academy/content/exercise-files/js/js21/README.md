# js21 · Order dashboard loader (async and await)

Build the data layer for the Ralfiz Store "My account" page. A fake API in
`index.js` behaves like real services: some calls are slow, one is flaky and
one is down.

## Run

```bash
cd start
node index.js
```

Node 22 or newer. The `package.json` one folder up sets `"type": "module"`,
so top-level `await` works in `index.js`.

## Tasks

Work through `TODO(1)` to `TODO(7)` in `start/index.js`:

1. Load profile, orders and offers in parallel with `Promise.all`.
2. Give recommendations a 500 ms budget with `AbortSignal.timeout`.
3. Write `retry()` with exponential backoff.
4. Use it to load the exchange rate.
5. Load the widgets with `Promise.allSettled` and report each one.
6. Send the invoice reminders one at a time with `for...of`.
7. Run everything inside one `try/catch`.

## Acceptance criteria

- The first line reads `Asha Menon: 3 orders, 2 offers in 300 ms` (not 900 ms).
- Recommendations print `skipped (took too long)` after about half a second.
- Two failed exchange-rate attempts are logged with delays of 100 ms and
  200 ms, then `Exchange rate: 1 INR = 0.012 USD`.
- Widgets print `profile ok`, `offers ok` and `loyalty FAILED: ...`.
- Reminders print in order INV-1, INV-2, INV-3 in about 500 ms.

Compare with `solution/index.js` when you are done.
