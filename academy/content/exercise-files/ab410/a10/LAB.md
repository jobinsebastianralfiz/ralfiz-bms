# AB-410 · A.10 Canvas apps: data, variables and collections

## Files
- shared-data/hd/tickets.csv
- start/state-and-data.txt
- solution/state-and-data.txt

## Steps
1. Download the exercise files. Open the student canvas app and check that Tickets and Categories are added as data sources.
2. Create four screens: scrHome, scrNew, scrDetail and scrSaved. Add the controls named in state-and-data.txt from the start folder (galTickets, lblHello, lblCount, icoSave, drpCategory, btnSubmit, lblTitle, tglEdit, txtDetailDesc, btnSave, galSaved, icoRemove).
3. Work through state-and-data.txt from the start folder top to bottom and replace each TODO with your own formula.
4. Run App.OnStart (right-click App > Run OnStart), then play scrHome and check the gallery and count against the check list below.
5. Paste the delegation experiment formula into galTickets.Items, read the warning, then undo it.
6. Submit a new ticket, open a ticket on scrDetail, edit its description with the toggle, and save two tickets for later then remove one.
7. Compare your formulas with state-and-data.txt in the solution folder and fix any differences that change behaviour.

## Check your work
- [ ] galTickets shows 4 tickets in this order: CHD-1017, CHD-1014, CHD-1009, CHD-1002, and lblCount reads “4 tickets”.
- [ ] The formula Filter(Tickets, Len(Title) > 20) shows a delegation warning and 26 rows; only CHD-1011 and CHD-1023 have titles of 20 characters or fewer.
- [ ] A ticket submitted from scrNew appears in the Ticket table with Priority Medium and Status Open, and the table has one more row than before (29 if you started with the 28 rows of tickets.csv).
- [ ] Saving the same ticket twice leaves one row in colSaved (check it under Variables > Collections).
- [ ] After Save on scrDetail the ticket description is updated in place, and the Ticket table still has the same number of rows.
