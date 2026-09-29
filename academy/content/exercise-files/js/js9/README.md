# js9 lab: Ticket Desk utilities (closures)

You are building small helpers for the Ralfiz help desk and billing app. Each
helper is a **factory**: a function that returns other functions sharing
private state through a closure.

## Run it

```bash
cd javascript/js9/start
node index.js
```

Node.js 22 or newer. No packages needed.

## Tasks

Work through `TODO(1)` to `TODO(6)` in `start/index.js`:

1. `makeIdGenerator(prefix, start)` returns IDs like `INV-0001`, `INV-0002`.
2. `makeCounter(start)` returns `{ increment, decrement, reset, value }`.
3. `once(fn)` runs `fn` the first time only and remembers its result.
4. `makeRateLimiter(limit)` allows `limit` actions, then returns `false`.
5. Fix `buildReminders()` so each reminder keeps its own hour.
6. Show that the counter's state is private.

## Acceptance criteria

- `INV-0001 INV-0002 INV-0003`, then `REC-0100` from an independent generator.
- Counter prints `11 12 11`, then `10` after `reset()`.
- The welcome email line appears exactly once.
- Rate limiter prints `[ true, true, true, false, false ]`.
- Reminders print `9:00`, `10:00`, `11:00`.

Compare with `solution/index.js` when you are done.