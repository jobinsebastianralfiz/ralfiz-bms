# PL-900 · 2.9 Monitoring and analytics

## Files
- monitoring-worksheet.md

## Steps
1. Download monitoring-worksheet.md.
2. In the admin center, find the capacity or licensing page and record Database, File and Log storage in Part A.
3. Open a canvas app on the Ticket table in edit mode (create one from data if you have none), then choose Advanced tools > Monitor.
4. Play the app: let the gallery load, select a ticket, edit and save it. Record the events you see in Part B.
5. Open any cloud flow (or build the test flow described in Part C) and read its 28-day run history.
6. Open one run and record each step’s result and one input or output value.
7. Complete Part D: choose the right tool for each problem.

## Check your work
- [ ] Monitor shows new data (network) events for the Ticket data source when the gallery loads.
- [ ] Saving an edited ticket adds a data event to Monitor with a successful result.
- [ ] The flow run history lists your runs with status Succeeded, and each step inside a run shows a green tick.
- [ ] In Part D, the slow app is Monitor, the failed flow is run history, storage is capacity, and "who changed it" is auditing.
