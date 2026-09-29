// Ralfiz Store API client (solution)
// Run: node index.js   (Node 22+, needs internet access)
// Optional: API_BASE=http://localhost:3000 node index.js

const BASE = process.env.API_BASE ?? 'https://dummyjson.com';

class ApiError extends Error {
  constructor(status, message, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

let token = null;

async function request(path, { method = 'GET', query, body, timeout = 8000 } = {}) {
  const url = new URL(path, BASE);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== '') url.searchParams.set(key, value);
  }

  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(timeout),
    });
  } catch (err) {
    const reason = err.name === 'TimeoutError' ? 'timed out' : 'network error';
    throw new Error(`${method} ${url.pathname}: ${reason}`, { cause: err });
  }

  const isJson = res.headers.get('content-type')?.includes('json');
  const data = isJson ? await res.json() : await res.text();
  if (!res.ok) throw new ApiError(res.status, data?.message ?? res.statusText, data);
  return data;
}

const api = {
  get: (path, query) => request(path, { query }),
  post: (path, body) => request(path, { method: 'POST', body }),
};

async function main() {
  const top = await api.get('/products', {
    sortBy: 'rating', order: 'desc', limit: 3, select: 'title,rating',
  });
  console.log('Top rated:');
  for (const p of top.products) console.log(`  ${p.title} (${p.rating})`);

  const found = await api.get('/products/search', { q: 'phone', limit: 2 });
  console.log(`Search "phone": ${found.total} found, showing ${found.products.length}`);

  try {
    await api.get('/products/9999');
  } catch (err) {
    if (!(err instanceof ApiError)) throw err;
    console.log(`Not found (${err.status}): ${err.message}`);
  }

  const created = await api.post('/products/add', {
    title: 'Ralfiz Steel Bottle', price: 18, category: 'kitchen-accessories',
  });
  console.log(`Created product #${created.id}: ${created.title}`);

  const session = await api.post('/auth/login', {
    username: 'emilys', password: 'emilyspass', expiresInMins: 30,
  });
  token = session.accessToken; // in a browser, think hard about where this lives
  const me = await api.get('/auth/me');
  console.log(`Logged in as ${me.username} (${me.email})`);
}

main().catch((err) => {
  console.error('Unexpected error:', err.message);
  process.exitCode = 1;
});
