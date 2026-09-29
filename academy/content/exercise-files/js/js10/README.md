# js10 lab: fix the Booking Desk (this, call, apply, bind)

A venue booking class for the Ralfiz events app works when you call its
methods directly, but breaks whenever a method is passed somewhere else.
A `safely()` helper catches each failure and prints a line starting with
`BUG`, so the script keeps running.

## Run it

```bash
cd javascript/js10/start
node index.js
```

Node.js 22 or newer. No packages needed.

## Tasks

Fix `TODO(1)` to `TODO(5)` in `start/index.js`:

1. `describeAll()` uses a regular function inside `map`.
2. The seats report passes `desk.seatsTaken` without its object.
3. The reminder passes `desk.remind` straight to `setTimeout`.
4. Borrow `describeOne` for a Hall B guest with `call`.
5. Make `printVip` with `bind` so the label is always `VIP`.

## Acceptance criteria

- No lines start with `BUG`.
- `describe: [ 'Asha x2 at Ralfiz Hall A', ... ]` lists all three bookings.
- `seats taken: 7`.
- `borrowed: Guest x3 at Ralfiz Hall B`.
- `VIP ticket for Asha (2 seats) at Ralfiz Hall A`.
- Last line: `Reminder: 3 bookings at Ralfiz Hall A`.

Compare with `solution/index.js` when you are done.