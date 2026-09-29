# Lab 2.1 - Ralfiz Stays booking quote

Write the pure pricing core for a hotel booking and a small impure shell that
prints quotes. Practise declarations, arrows, defaults, the options object,
rest parameters, spread and JSDoc.

## Run it

    cd javascript/js8/start
    node index.js

## Pricing rules

- Room rate is passed in (3200 for the Garden View Suite).
- Friday and Saturday nights cost 20% more (rounded to whole rupees).
- More than 2 guests: ₹800 per extra guest per night.
- Add-ons are flat prices, passed as an array.
- Coupons: RALFIZ10 = 10% off the total (rounded); STAY500 = ₹500 off,
  never below ₹0. Codes are case-insensitive; unknown codes do nothing.

## Acceptance criteria

- nightsBetween('2026-10-09', '2026-10-12') is 3 and the reversed dates give 0
- countWeekendNights('2026-10-09', 3) is 2
- addOnsTotal() is 0 and addOnsTotal(1200, 900) is 2100
- Quote A (3 nights, 2 guests, pickup, no coupon) totals ₹12,080
- Quote B (2 nights, 4 guests, both add-ons, RALFIZ10) totals ₹10,530
- The purity check prints Same result twice: true and Input unchanged: true
