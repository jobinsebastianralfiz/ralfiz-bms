# PL-900 · 4.3 Triggers, actions and connectors

## Files
- flow-spec.md
- test-tickets.csv

## Steps
1. Complete the three Flow Builder scenarios above.
2. Download the exercise files and read flow-spec.md. Note which connectors in it are standard and which are premium.
3. In the Ticket table, find the number for the High option of Priority and write it in flow-spec.md as HIGH_VALUE.
4. In Power Automate, create CHD - High priority alert with the Dataverse trigger When a row is added, modified or deleted (Added, Tickets, Organization).
5. Add a Condition: Priority is equal to HIGH_VALUE.
6. In the Yes branch, add Send an email (V2) to yourself with the concat subject and the body from flow-spec.md.
7. Add the 3 rows of test-tickets.csv to Ticket one at a time, then open the run history and answer the 3 questions in flow-spec.md.

## Check your work
- [ ] The run history shows 3 succeeded runs, one per test ticket.
- [ ] You received 2 emails: High priority ticket: Server room air conditioning alarm and High priority ticket: Exam hall Wi-Fi down.
- [ ] In the run for Poster printer out of paper, the condition result is false and the email action did not run.
- [ ] Each email body shows a Logged at (UTC) time in yyyy-MM-dd HH:mm format.
