// js9 lab: Ticket Desk utilities. Run with: node index.js

function makeIdGenerator(prefix, start = 1) {
  let next = start;
  return () => `${prefix}-${String(next++).padStart(4, '0')}`;
}

function makeCounter(start = 0) {
  let count = start;
  return {
    increment: () => ++count,
    decrement: () => --count,
    reset: () => { count = start; },
    value: () => count,
  };
}

function once(fn) {
  let called = false;
  let result;
  return (...args) => {
    if (!called) {
      called = true;
      result = fn(...args);
    }
    return result;
  };
}

function makeRateLimiter(limit) {
  let used = 0;
  return () => {
    if (used >= limit) return false;
    used += 1;
    return true;
  };
}

function buildReminders() {
  const reminders = [];
  // let creates a new hour binding for every iteration
  for (let hour = 9; hour < 12; hour++) {
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

// count lives in makeCounter's environment, not on the returned object,
// so there is no property to read: the state is private.
console.log('typeof counter.count:', typeof counter.count);