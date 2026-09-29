// js9 lab: Ticket Desk utilities. Run with: node index.js

// TODO(1): return a function that returns PREFIX-0001, PREFIX-0002, ...
// Hint: keep a private next number and use String(n).padStart(4, '0').
function makeIdGenerator(prefix, start = 1) {
  return () => `${prefix}-????`;
}

// TODO(2): return { increment, decrement, reset, value } sharing ONE count.
// reset() goes back to the start value.
function makeCounter(start = 0) {
  return {
    increment: () => start,
    decrement: () => start,
    reset: () => start,
    value: () => start,
  };
}

// TODO(3): run fn on the first call only; later calls return the first result.
function once(fn) {
  return fn;
}

// TODO(4): allow limit calls (return true), then return false forever.
function makeRateLimiter(limit) {
  return () => true;
}

// TODO(5): each reminder should remember its own hour.
function buildReminders() {
  const reminders = [];
  for (var hour = 9; hour < 12; hour++) {
    reminders.push(() => `Standup reminder at ${hour}:00`);
  }
  return reminders;
}

// ---- Try it ----
const nextInvoice = makeIdGenerator('INV');
const nextReceipt = makeIdGenerator('REC', 100);
console.log(nextInvoice(), nextInvoice(), nextInvoice());
console.log(nextReceipt());

const counter = makeCounter(10);
console.log(counter.increment(), counter.increment(), counter.decrement());
counter.reset();
console.log('after reset:', counter.value());

const sendWelcome = once((email) => {
  console.log('Sending welcome email to', email);
  return 'sent';
});
sendWelcome('asha@ralfiz.dev');
sendWelcome('asha@ralfiz.dev');
console.log('third call:', sendWelcome('asha@ralfiz.dev'));

const allowOtp = makeRateLimiter(3);
console.log([1, 2, 3, 4, 5].map(() => allowOtp()));

for (const remind of buildReminders()) console.log(remind());

// TODO(6): log typeof counter.count and explain why it is undefined.