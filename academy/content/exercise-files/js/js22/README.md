# js22 · Ralfiz Store API client (fetch)

Write a small, reusable API client for DummyJSON in Node, then use it for
reads, a search, a 404, a create and an authenticated request.

## Run

```bash
cd start
node index.js
```

You need Node 22+ (it has `fetch` built in) and internet access. The client
reads its base URL from `API_BASE`, which defaults to `https://dummyjson.com`.

## Tasks

Complete `TODO(1)` to `TODO(10)` in `start/index.js`:

- an `ApiError` class that keeps the HTTP status,
- a `request()` function that builds the URL with `URL` and
  `URLSearchParams`, sends JSON, adds the Bearer token, checks
  `response.ok` and times out after 8 seconds,
- five calls that use it.

## Acceptance criteria

- `Top rated:` is followed by three `title (rating)` lines, highest first.
- `Search "phone": N found, showing 2`.
- `Not found (404): Product with id '9999' not found`.
- `Created product #195: Ralfiz Steel Bottle` (DummyJSON does not really
  save it, so the id is always the next free one).
- `Logged in as emilys (...)` after the login.
- Turning off your internet prints a clear `network error` message instead
  of a stack trace.

Compare with `solution/index.js` when you are done.
