# js27 – Refactor the festive checkout

start/index.js is a real-world style messy script: one go() function handles
pricing, coupons, shipping, stock warnings, receipts, email and logging.
Refactor it into a pure core and an imperative shell WITHOUT changing its output.

## Run

    cd javascript/js27/start
    node index.js > before.txt

Keep before.txt: it is your safety net. After each step, run the script again
and compare (for example with "diff before.txt after.txt", or VS Code's
"Compare Selected").

## Tasks

- TODO(1) names and constants
- TODO(2) parseCoupon returning a result object
- TODO(3) shipping strategy map (unknown methods throw)
- TODO(4) pure priceOrder
- TODO(5) events: stock:low, coupon:rejected, order:placed
- TODO(6) pure formatReceipt returning lines
- TODO(7) split into checkout.js (core) and index.js (shell) with
  "type": "module" in package.json

## Acceptance criteria

- node index.js prints exactly the same text before and after the refactor
  (Anu's total is 4522.76 and Ravi's is 283.20).
- checkout.js never uses console, Date or Math.random, and never mutates
  the order it receives.
- Adding a new delivery method is one new entry in shippingStrategies.
- An unknown delivery method throws "Unknown shipping method: …".
