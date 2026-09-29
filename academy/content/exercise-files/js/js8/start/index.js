// Lab 2.1 - Ralfiz Stays booking quote (starter)
// Run: node index.js

const WEEKEND_UPLIFT = 0.2;
const EXTRA_GUEST_FEE = 800;
const DAY_MS = 24 * 60 * 60 * 1000;
const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
});

// TODO(1): function declaration. Use Date.parse(iso + 'T00:00:00Z') for both
// dates, divide the difference by DAY_MS, return 0 unless it is > 0.
function nightsBetween(checkIn, checkOut) {
  return 0;
}

// TODO(2): loop i from 0 to nights - 1, build the UTC date of each night
// and count the ones where getUTCDay() is 5 (Friday) or 6 (Saturday).
function countWeekendNights(checkIn, nights) {
  return 0;
}

// TODO(3): arrow function with a rest parameter ...prices; return the sum.
const addOnsTotal = () => 0;

// TODO(4): default code = ''. Normalise with trim().toUpperCase().
// RALFIZ10 -> Math.round(amount * 0.9); STAY500 -> Math.max(0, amount - 500).
function applyCoupon(amount, code) {
  return amount;
}

// TODO(5): destructure { checkIn, checkOut, rate, guests = 2, addOns = [],
// coupon = '' } = {} in the parameter list. Return a NEW object:
// { nights, weekendNights, room, extraGuests, addOns, total }.
// TODO(6): add a JSDoc comment above this function.
function quote(options) {
  return { nights: 0, weekendNights: 0, room: 0, extraGuests: 0, addOns: 0, total: 0 };
}

// TODO(6): JSDoc here too. Return a multi-line string for printing.
function formatQuote(label, q) {
  return `${label}: ${inr.format(q.total)}`;
}

// ---------- impure shell ----------
const bookingA = {
  checkIn: '2026-10-09', checkOut: '2026-10-12', rate: 3200, addOns: [1200],
};
const bookingB = {
  checkIn: '2026-11-18', checkOut: '2026-11-20', rate: 3200, guests: 4,
  addOns: [1200, 900], coupon: 'ralfiz10',
};

console.log('nights:', nightsBetween('2026-10-09', '2026-10-12'),
  nightsBetween('2026-10-12', '2026-10-09'));
console.log('weekend nights:', countWeekendNights('2026-10-09', 3));
console.log('add-ons:', addOnsTotal(), addOnsTotal(1200, 900));
console.log(formatQuote('Quote A', quote(bookingA)));
console.log(formatQuote('Quote B', quote(bookingB)));

// TODO(7): prove purity. Save JSON.stringify(bookingB), call quote twice,
// compare the two results as JSON, and compare bookingB with the saved JSON.
