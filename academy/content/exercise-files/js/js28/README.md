# js28 – Test the Ralfiz cart with Vitest

cart.js is a real ES module: createCart (add, remove, items, applyCoupon,
totals, async checkout) and a debounce helper. cart.test.js has three passing
tests and it.todo entries. You will write the missing tests, find one bug and
build one feature test-first.

## Set up (once, inside the start folder)

    cd javascript/js28/start
    npm init -y
    npm pkg set type=module
    npm pkg set scripts.test=vitest
    npm install -D vitest

Then run:

    npx vitest          # watch mode: reruns on every save
    npx vitest run      # run once (what CI does)

Node.js 22 or newer. Optional coverage report:

    npx vitest run --coverage   # installs @vitest/coverage-v8 when asked

## Tasks

- TODO(1)–TODO(2): error paths with toThrow (the stock test fails until TODO(3)
  is fixed, because a repeat add overwrites the quantity).
- TODO(3): the repeat-add test. It FAILS against cart.js: fix add() so
  quantities add up and the stock check uses the new total.
- TODO(4): rounding with toBeCloseTo.
- TODO(5): TDD. Write the coupon cap test, see it fail (discount 1250),
  then change totals() to use Math.min(…, coupon.max ?? Infinity).
- TODO(6): expiry with an injected clock, then with vi.setSystemTime.
- TODO(7): checkout with vi.fn().mockResolvedValue / mockRejectedValue.
- TODO(8): debounce with vi.useFakeTimers and vi.advanceTimersByTime.

## Acceptance criteria

- npx vitest run shows 17 passed and 0 failed with your tests
  (compare with solution/cart.test.js).
- Replacing your cart.js add() with the original buggy line makes the
  repeat-add test fail with "expected 3 to be 5".
- No test waits for real time or calls a real payment or network API.
