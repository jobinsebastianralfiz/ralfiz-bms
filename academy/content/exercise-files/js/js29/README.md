# js29 Lab: a typed Ralfiz Store order module

Turn a loosely typed order script into strict, safe TypeScript.

## What you practise
- literal union types (`Category`, `OrderStatus`)
- a discriminated union (`Payment`) with an exhaustive `switch` and `assertNever`
- a generic function (`groupBy`)
- a `Result<T>` type instead of throwing for expected failures
- a type guard (`isProduct(x: unknown): x is Product`) for JSON from outside

## How to run
You need Node.js 22 or newer.

```bash
cd start
npx -p typescript tsc -p .     # type-check and compile to dist/
node dist/index.js             # run the compiled JavaScript
```

Prefer a local install in real projects: `npm init -y`, then
`npm install -D typescript` and `npx tsc -p .`.
Do not run a bare `npx tsc` without TypeScript installed: it downloads an
unrelated package called `tsc`.

Node 22.18 and later can also run `node index.ts` directly. Node only strips
the types and does not check them, so still run `tsc` (or `tsc --noEmit`).

## Tasks
Work through `TODO(1)` to `TODO(6)` in `start/index.ts`. After each one, run
`tsc -p .` and fix every error before moving on.

For TODO(3), add a fourth payment kind such as `{ kind: 'wallet' }` to the
union and check that `tsc` reports every switch that does not handle it. Then
remove it again.

## Acceptance criteria
- `tsc -p .` finishes with no errors and there is no `any` left in the file.
- `node dist/index.js` prints two Skipped lines (not enough Gel Pens, no product 99).
- The summary line reads `Subtotal ₹1,793 | RUPAY card ending 4242 fee ₹32 | Total ₹1,825`.
- It prints one line per category group: books, electronics and stationery.
- The last line reads `API payload: 1 valid of 2: Desk Lamp`.
