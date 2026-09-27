# AB-410 · A.11 Canvas apps: reusable components and design quality

## Files
- cmpHeader-spec.md
- start/app-formulas.txt
- solution/app-formulas.txt

## Steps
1. Download the exercise files. In the Campus Help Desk solution, create the component library Campus UI.
2. Build cmpHeader with the properties and control formulas in cmpHeader-spec.md, then save and publish the library.
3. Import cmpHeader into the student app and place it on each screen with the Title, ShowBack and OnBack values from the table in cmpHeader-spec.md.
4. Open app-formulas.txt from the start folder, paste the OnStart formula into App.OnStart, and fill in TODO 1 to 6 in App.Formulas.
5. Use the named formulas and functions in galTickets and lblOpen, replace every varBlue with ThemeBlue, and trim OnStart to a single Concurrent call.
6. Turn off Scale to fit, rebuild scrHome with conMain and conFilters, and set the widths listed in the solution file.
7. Set the AccessibleLabel values, run the App checker, and tick every line of the design-quality checklist in cmpHeader-spec.md.
8. Record a Monitor session before and after the OnStart change, then compare your App.Formulas with app-formulas.txt in the solution folder.

## Check your work
- [ ] A temporary label with DueLabel(Date(2030, 1, 15)) shows “Due 15 Jan”.
- [ ] Every row in galTickets shows “Overdue”, because every Due Date in tickets.csv is on or before 3 Sep 2026.
- [ ] lblOpen shows 6 open tickets, plus any tickets with Status Open you created in A.10.
- [ ] If you imported tickets.csv yourself, MyOpenTickets returns 12 rows (6 Open and 6 In progress), plus the tickets you submitted in A.10.
- [ ] The App checker lists 0 accessibility issues, and on scrHome the header’s back icon is hidden.
