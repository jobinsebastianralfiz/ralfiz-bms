// Ralfiz Store: order dashboard loader (starter)
// Run: node index.js   (Node 22+)

// ---- Fake API: behaves like real services (do not edit) ----
function sleep(ms, signal) {
  return new Promise((resolve, reject) => {
    signal?.throwIfAborted();
    const id = setTimeout(resolve, ms);
    signal?.addEventListener('abort', () => {
      clearTimeout(id);
      reject(signal.reason);
    }, { once: true });
  });
}

let rateCalls = 0;
const api = {
  async getProfile(signal) {
    await sleep(300, signal);
    return { name: 'Asha Menon', city: 'Kochi' };
  },
  async getOrders(signal) {
    await sleep(300, signal);
    return [
      { id: 'ORD-101', total: 2499 },
      { id: 'ORD-102', total: 899 },
      { id: 'ORD-103', total: 4150 },
    ];
  },
  async getOffers(signal) {
    await sleep(300, signal);
    return ['FEST10', 'FREESHIP'];
  },
  async getRecommendations(signal) {
    await sleep(2000, signal); // a slow service
    return ['Steel bottle', 'Laptop sleeve'];
  },
  async getExchangeRate(signal) {
    rateCalls += 1;
    await sleep(100, signal);
    if (rateCalls < 3) throw new Error('503 Service Unavailable');
    return 0.012; // 1 INR in USD
  },
  async getLoyalty(signal) {
    await sleep(150, signal);
    throw new Error('Loyalty service is down');
  },
  async sendReminder(invoiceId) {
    await sleep(150);
    return invoiceId + ' reminded';
  },
};

const since = (t0) => Math.round((performance.now() - t0) / 100) * 100 + ' ms';

// ---- Your code ----

// TODO(1): load profile, orders and offers IN PARALLEL with Promise.all.
// Log: "Asha Menon: 3 orders, 2 offers in 300 ms" (use since(t0)).
async function loadDashboard() {
  const t0 = performance.now();
  const profile = await api.getProfile();
  const orders = await api.getOrders();
  const offers = await api.getOffers();
  console.log(profile.name + ': ' + orders.length + ' orders, ' +
    offers.length + ' offers in ' + since(t0));
}

// TODO(2): give recommendations a 500 ms budget with AbortSignal.timeout(500).
// On TimeoutError log "Recommendations: skipped (took too long)".
async function loadRecommendations() {
  console.log('Recommendations: TODO');
}

// TODO(3): write retry(fn, { retries, base }) with exponential backoff:
// wait base, base*2, base*4 ms between attempts, log each failed attempt,
// and rethrow after the last attempt.
async function retry(fn, { retries = 3, base = 100 } = {}) {
  return fn();
}

// TODO(4): use retry() to get the exchange rate and log
// "Exchange rate: 1 INR = 0.012 USD".
async function loadRate() {
  console.log('Exchange rate: TODO');
}

// TODO(5): load profile, offers and loyalty with Promise.allSettled.
// Log one line per widget: "  profile ok" or "  loyalty FAILED: <message>".
async function loadWidgets() {
  console.log('Widgets: TODO');
}

// TODO(6): send reminders for INV-1, INV-2, INV-3 ONE AT A TIME (for...of)
// and log the results array plus the time taken.
async function sendReminders() {
  console.log('Reminders: TODO');
}

// TODO(7): run the steps in order and catch any unexpected error.
await loadDashboard();
await loadRecommendations();
await loadRate();
await loadWidgets();
await sendReminders();
