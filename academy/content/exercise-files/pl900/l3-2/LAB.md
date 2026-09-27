# PL-900 · 3.2 Model-driven apps

## Files
- shared-data/hd/tickets.csv
- app-spec.md

## Steps
1. Download the exercise files and read app-spec.md. Make sure Ticket holds the 28 rows from tickets.csv.
2. In the Ticket table properties, check that quick create forms are enabled.
3. Create a blank model-driven app named Help Desk Staff.
4. Add a Dataverse table page for Ticket and one for Category, grouped as in the navigation table of app-spec.md.
5. Open the Ticket page’s forms and views in the app designer and make sure the main form, the quick create form and the Open high-priority tickets view are included.
6. Save and publish, then play the app and run acceptance tests 1 to 4 in app-spec.md.
7. Optional: on Active Tickets, show the chart pane and create a column chart counting tickets by Priority (test 5).

## Check your work
- [ ] Active Tickets shows 28 rows before you add anything.
- [ ] Open high-priority tickets shows 0 rows at first, because no ticket in tickets.csv is both Open and High.
- [ ] After adding Tablet screen cracked with quick create, Open high-priority tickets shows exactly 1 row.
- [ ] The optional Priority chart shows Medium 14, Low 10 and High 5.
