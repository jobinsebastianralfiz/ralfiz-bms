# AB-410 · A.17 Business rules, process flows and calculated columns

## Files
- shared-data/hd/tickets.csv
- logic-placement-brief.md
- formula-column.txt

## Steps
1. Complete the “Where should this logic live?” sorter above.
2. Download the exercise files and fill in the Your choice and Reason columns for R1 to R8 in logic-placement-brief.md.
3. Build the R1 business rule on Ticket with scope Entity and activate it. Test it in Help Desk Staff by setting CHD-1025 to High and clearing its Due Date.
4. Build the quick flow from formula-column.txt and run it to prove the rule also applies outside forms.
5. Add the chd_daysopen formula column from formula-column.txt and add it to the Active Tickets view.
6. Add the chd_opentickets rollup column to Category, add it to the Categories view, and refresh it on each category.
7. Create the Ticket lifecycle business process flow from the R4 table, activate it, add it to Help Desk Staff and move CHD-1024 through every stage. Set CHD-1025 back to Medium afterwards.

## Check your work
- [ ] Saving CHD-1025 as High with no Due Date shows “High priority tickets need a due date.” on the form.
- [ ] The quick flow’s Add a new row action fails with the same message, and succeeds once a Due Date is given.
- [ ] After refresh, Open Tickets reads Accounts 1, Classroom AV 1, Hardware 1, Network 2, Printing 1, Software 0.
- [ ] Days open is empty for the 16 Closed tickets and shows a number for the other 12.
- [ ] CHD-1024 cannot move from Resolved to Closed until Resolution Notes is filled in.
