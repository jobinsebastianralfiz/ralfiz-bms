// Lab 2.1 - Ralfiz Stays booking quote (solution)
// Run: node index.js

const WEEKEND_UPLIFT = 0.2;
const EXTRA_GUEST_FEE = 800;
const DAY_MS = 24 * 60 * 60 * 1000;
const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
});

const toUtc = (iso) => Date.parse(`${iso}T00:00:00Z`);

function nightsBetween(checkIn, checkOut) {
  const nights = (toUtc(checkOut) - toUtc(checkIn)) / DAY_MS;
  return Number.isFinite(nights) && nights > 0 ? nights : 0;
}

function countWeekendNights(checkIn, nights) {
  let count = 0;
  for (let i = 0; i < nights; i++) {
    const day = new Date(toUtc(checkIn) + i * DAY_MS).getUTCDay();
    if (day === 5 || day === 6) count++;
  }
  return count;
}

const addOnsTotal = (...prices) => {
  let total = 0;
  for (const price of prices) total += price;
  return total;
};

function applyCoupon(amount, code = '') {
  switch (code.trim().toUpperCase()) {
    case 'RALFIZ10':
      return Math.round(amount * 0.9);
    case 'STAY500':
      return Math.max(0, amount - 500);
    default:
      return amount;
  }
}

/**
 * Price a stay. Pure: it reads only its argument and returns a new object.
 * @param {object} options
 * @param {string} options.checkIn ISO date such as '2026-10-09'
 * @param {string} options.checkOut ISO date after checkIn
 * @param {number} options.rate nightly rate in rupees
 * @param {number} [options.guests=2]
 * @param {number[]} [options.addOns=[]] flat add-on prices
 * @param {string} [options.coupon=''] RALFIZ10 or STAY500
 * @returns {{nights: number, weekendNights: number, room: number,
 *   extraGuests: number, addOns: number, total: number}}
 */
function quote({ checkIn, checkOut, rate, guests = 2, addOns = [], coupon = '' } = {}) {
  const nights = nightsBetween(checkIn, checkOut);
  const weekendNights = countWeekendNights(checkIn, nights);
  const room = nights * rate + Math.round(weekendNights * rate * WEEKEND_UPLIFT);
  const extraGuests = Math.max(0, guests - 2) * EXTRA_GUEST_FEE * nights;
  const extras = addOnsTotal(...addOns);
  const total = applyCoupon(room + extraGuests + extras, coupon);
  return { nights, weekendNights, room, extraGuests, addOns: extras, total };
}

/**
 * Format a quote for the console.
 * @param {string} label
 * @param {ReturnType<typeof quote>} q
 * @returns {string}
 */
function formatQuote(label, q) {
  return `${label}: ${q.nights} nights (${q.weekendNights} weekend)
  Room         ${inr.format(q.room)}
  Extra guests ${inr.format(q.extraGuests)}
  Add-ons      ${inr.format(q.addOns)}
  Total        ${inr.format(q.total)}`;
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

const before = JSON.stringify(bookingB);
const first = JSON.stringify(quote(bookingB));
const second = JSON.stringify(quote(bookingB));
console.log('Same result twice:', first === second);
console.log('Input unchanged:', JSON.stringify(bookingB) === before);
