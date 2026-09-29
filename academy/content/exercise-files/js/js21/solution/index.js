// Ralfiz Store: order dashboard loader (solution)
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

// ---- Solution ----

async function loadDashboard() {
  const t0 = performance.now();
  const [profile, orders, offers] = await Promise.all([
    api.getProfile(),
    api.getOrders(),
    api.getOffers(),
  ]);
  console.log(profile.name + ': ' + orders.length + ' orders, ' +
    offers.length + ' offers in ' + since(t0));
}

async function loadRecommendations() {
  try {
    const items = await api.getRecommendations(AbortSignal.timeout(500));
    console.log('Recommendations:', items);
  } catch (err) {
    if (err.name !== 'TimeoutError') throw err;
    console.log('Recommendations: skipped (took too long)');
  }
}

async function retry(fn, { retries = 3, base = 100 } = {}) {
  for (let attempt = 1; ; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt > retries) throw err;
      const delay = base * 2 ** (attempt - 1);
      console.log('  attempt ' + attempt + ' failed (' + err.message +
        '), retrying in ' + delay + ' ms');
      await sleep(delay);
    }
  }
}

async function loadRate() {
  const rate = await retry(() => api.getExchangeRate(), { retries: 3, base: 100 });
  console.log('Exchange rate: 1 INR = ' + rate + ' USD');
}

async function loadWidgets() {
  const names = ['profile', 'offers', 'loyalty'];
  const results = await Promise.allSettled([
    api.getProfile(),
    api.getOffers(),
    api.getLoyalty(),
  ]);
  console.log('Widgets:');
  results.forEach((r, i) => {
    console.log(r.status === 'fulfilled'
      ? '  ' + names[i] + ' ok'
      : '  ' + names[i] + ' FAILED: ' + r.reason.message);
  });
}

async function sendReminders() {
  const t0 = performance.now();
  const results = [];
  for (const id of ['INV-1', 'INV-2', 'INV-3']) {
    results.push(await api.sendReminder(id)); // one at a time
  }
  console.log('Reminders:', results, 'in ' + since(t0));
}

try {
  await loadDashboard();
  await loadRecommendations();
  await loadRate();
  await loadWidgets();
  await sendReminders();
} catch (err) {
  console.error('Dashboard failed:', err.message);
  process.exitCode = 1;
}
