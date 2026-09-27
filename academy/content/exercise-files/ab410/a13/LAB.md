# AB-410 · A.13 Cloud flows: triggers, connectors and actions

## Files
- shared-data/hd/tickets.csv
- flow-test-cases.md
- email-expressions.txt

## Steps
1. Complete the “Which trigger fits?” sorter above.
2. Download the exercise files. In the Campus Help Desk solution, create the automated cloud flow Notify on high priority ticket with the Dataverse trigger When a row is added, modified or deleted (Added or Modified, Tickets, Organization).
3. Look up the numeric value of High in the Priority choice, then set Select columns and Filter rows as shown at the top of flow-test-cases.md.
4. Add Get a row by ID on Categories and Send an email (V2), pasting the expressions from email-expressions.txt.
5. Save the flow and note the current number of runs in the run history.
6. Run tests T1 to T6 from flow-test-cases.md in the Help Desk Staff app, filling in the Expected columns as you go.
7. Open the T1 run and inspect the three points listed under What to inspect in run history, then do the clean-up.

## Check your work
- [ ] Tests T1 to T6 create exactly 3 new runs (T1, T5 and T6); T2, T3 and T4 create none.
- [ ] The T1 email subject is “High priority: Wi-Fi keeps disconnecting in the library” and it includes Category: Network and Due: 31 Aug 2026.
- [ ] The T6 email includes Category: Network and Due: 03 Sep 2026.
- [ ] In the T1 trigger outputs, chd_priority is a number, not the text High.
