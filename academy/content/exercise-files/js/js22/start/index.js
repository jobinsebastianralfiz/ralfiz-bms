// Ralfiz Store API client (starter)
// Run: node index.js   (Node 22+, needs internet access)
// Optional: API_BASE=http://localhost:3000 node index.js

const BASE = process.env.API_BASE ?? 'https://dummyjson.com';

// TODO(1): make ApiError extend Error and store status and data.
class ApiError {
  constructor(status, message, data) {
    this.message = message;
  }
}

// TODO(2): build the URL with new URL(path, BASE) and add every query
// value that is not undefined or '' with url.searchParams.set.
// TODO(3): add Content-Type: application/json and JSON.stringify(body)
// when there is a body, and Authorization: Bearer <token> when a token is set.
// TODO(4): if !res.ok, throw new ApiError(res.status, data.message, data).
// TODO(5): give every request an 8-second timeout with AbortSignal.timeout.
let token = null;
async function request(path, { method = 'GET', query, body } = {}) {
  const res = await fetch(BASE + path, { method });
  return res.json();
}

async function main() {
  // TODO(6): list the 3 top-rated products (sortBy=rating, order=desc,
  // limit=3, select=title,rating) and print "title (rating)" lines.
  const top = await request('/products?limit=3');
  console.log('Top rated:', top.products.map((p) => p.title));

  // TODO(7): search for "phone" (limit 2) and print how many were found.

  // TODO(8): request product 9999 and print "Not found (404): <message>".

  // TODO(9): POST /products/add with a new Ralfiz product and print its id.

  // TODO(10): log in as emilys / emilyspass, store the accessToken,
  // then GET /auth/me and print the username.
}

main().catch((err) => {
  console.error('Unexpected error:', err.message);
  process.exitCode = 1;
});
