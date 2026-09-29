// js20 · From callbacks to promises (solution)
// Run: node index.js

// ---------- Legacy callback API (unchanged) ----------
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

// ---------- 1. promisify ----------
const promisify = (fn) => (...args) =>
  new Promise((resolve, reject) => {
    fn(...args, (err, result) => (err ? reject(err) : resolve(result)));
  });

const getUserP = promisify(getUser);
const getOrdersP = promisify(getOrders);
const getStockP = promisify(getStock);
const getReviewsP = promisify(getReviews);
const slowReportP = promisify(slowReport);

// ---------- 2. a flat chain with one catch ----------
function userSummary(id) {
  return getUserP(id)
    .then((user) => getOrdersP(user.id).then((orders) => ({ user, orders })))
    .then(({ user, orders }) => ({
      name: user.name,
      orders: orders.length,
      total: orders.reduce((sum, o) => sum + o.total, 0),
    }))
    .catch(() => ({ name: 'unknown', orders: 0, total: 0 }));
}

// ---------- 3. parallel with Promise.all ----------
function loadDashboard() {
  const t0 = performance.now();
  return Promise.all([userSummary(7), getStockP('SKU-1'), getStockP('SKU-2')]).then(
    ([summary, sku1, sku2]) => ({
      summary,
      stock: { 'SKU-1': sku1, 'SKU-2': sku2 },
      tookMs: Math.round((performance.now() - t0) / 10) * 10,
    }),
  );
}

// ---------- 4. partial failure with allSettled ----------
function loadWithReviews() {
  return Promise.allSettled([getStockP('SKU-1'), getReviewsP()]).then((results) =>
    results.map((r) => (r.status === 'fulfilled' ? `fulfilled (${r.value})` : `rejected (${r.reason.message})`)),
  );
}

// ---------- 5. a timeout built from race ----------
function withTimeout(promise, ms) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`Timed out after ${ms} ms`)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

// ---------- 6. withResolvers ----------
function requestApproval() {
  const { promise, resolve } = Promise.withResolvers();
  setTimeout(() => resolve('Meera'), 100); // imagine a manager clicking Approve
  return promise;
}

// ---------- Run everything in order: each step returns its promise ----------
userSummary(7)
  .then((s) => console.log('Summary for 7: ', s))
  .then(() => userSummary(99))
  .then((s) => console.log('Summary for 99:', s))
  .then(() => loadDashboard())
  .then((d) => {
    console.log('Dashboard stock:', d.stock);
    console.log(`Dashboard took about ${d.tookMs} ms (the slowest call is 140 ms; one by one would be about 220 ms)`);
  })
  .then(() => loadWithReviews())
  .then((statuses) => console.log('allSettled:', statuses))
  .then(() => withTimeout(slowReportP(), 200))
  .then((report) => console.log('Report:', report))
  .catch((err) => console.log('withTimeout:', err.message))
  .then(() => requestApproval())
  .then((who) => console.log(`Approved by ${who}`))
  .finally(() => console.log('All sections finished.'));
