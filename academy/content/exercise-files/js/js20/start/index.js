// js20 · From callbacks to promises
// Run: node index.js

// ---------- Legacy callback API (do not change) ----------
const DB = {
  users: { 7: { id: 7, name: 'Anu' }, 8: { id: 8, name: 'Rahul' } },
  orders: {
    7: [{ id: 'A-101', total: 1499 }, { id: 'A-102', total: 650 }, { id: 'A-107', total: 3200 }],
    8: [],
  },
  stock: { 'SKU-1': 12, 'SKU-2': 0 },
};

function getUser(id, cb) {
  setTimeout(() => (DB.users[id] ? cb(null, { ...DB.users[id] }) : cb(new Error(`User ${id} not found`))), 60);
}
function getOrders(userId, cb) {
  setTimeout(() => cb(null, DB.orders[userId] ?? []), 80);
}
function getStock(sku, cb) {
  setTimeout(() => (sku in DB.stock ? cb(null, DB.stock[sku]) : cb(new Error(`Unknown ${sku}`))), 40);
}
function getReviews(cb) {
  setTimeout(() => cb(new Error('Reviews service is down')), 50);
}
function slowReport(cb) {
  setTimeout(() => cb(null, 'Annual report'), 500);
}

// ---------- Part 0: the pyramid (works, but hard to extend) ----------
function userSummaryCallback(id, done) {
  getUser(id, (err, user) => {
    if (err) return done(err);
    getOrders(user.id, (err, orders) => {
      if (err) return done(err);
      const total = orders.reduce((sum, o) => sum + o.total, 0);
      done(null, { name: user.name, orders: orders.length, total });
    });
  });
}

// ---------- Your promise versions ----------
// TODO(1): promisify(fn) → (...args) => new Promise(...)
const promisify = (fn) => (...args) => Promise.resolve(null);

// TODO(2): userSummary(id) as one flat chain with a single catch
const userSummary = (id) => Promise.resolve('TODO(2)');

// TODO(3): loadDashboard() with Promise.all
const loadDashboard = () => Promise.resolve('TODO(3)');

// TODO(4): loadWithReviews() with Promise.allSettled
const loadWithReviews = () => Promise.resolve('TODO(4)');

// TODO(5): withTimeout(promise, ms) with Promise.race
const withTimeout = (promise) => promise;

// TODO(6): an approval made with Promise.withResolvers, approved after 100 ms

userSummaryCallback(7, (err, summary) => {
  console.log('Pyramid version:', err ? err.message : summary);
  userSummary(7)
    .then((s) => console.log('Promise version:', s))
    .then(() => loadDashboard())
    .then((d) => console.log('Dashboard:', d))
    .then(() => loadWithReviews())
    .then((r) => console.log('With reviews:', r))
    .then(() => withTimeout(Promise.resolve('TODO(5)'), 200))
    .then((r) => console.log('Timeout:', r));
});
