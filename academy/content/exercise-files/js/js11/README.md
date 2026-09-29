# js11 lab: Tip and Bill Splitter utilities

Build small, pure, reusable helpers for a restaurant billing tool, then
combine them with `pipe`. All money is kept in **integer paise** so there
are no floating-point errors.

## Run it

```bash
cd javascript/js11/start
node index.js
```

Node.js 22 or newer. No packages needed.

## Tasks

Complete `TODO(1)` to `TODO(6)` in `start/index.js`:

1. `pipe(...fns)` runs functions left to right.
2. Curried `addPercent(pct)(paise)` and `discountFlat(paiseOff)(paise)`.
3. `roundUpTo(stepPaise)(paise)`.
4. `splitEvenly(people)(total)`: whole-paise shares that add up exactly.
5. `makeBillCalculator(options)` returns a configured pipeline.
6. Prove the order object is never mutated.

## Acceptance criteria

- `Subtotal: ₹1,200.00`.
- Tip table: ₹1,200.00, ₹1,260.00, ₹1,320.00, ₹1,380.00 (0, 5, 10, 15%).
- `Total to pay: ₹1,280.00` and shares `₹426.67, ₹426.67, ₹426.66`.
- `Shares add up: true` and `Order unchanged: true`.

Compare with `solution/index.js` when you are done.