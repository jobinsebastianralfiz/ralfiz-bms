# PL-900 · 2.1 Dataverse vs a traditional database

## Files
- shared-data/hd/tickets.csv
- excel-vs-dataverse.md

## Steps
1. Download tickets.csv and excel-vs-dataverse.md.
2. Open tickets.csv in Excel and answer Part A questions 1 and 2.
3. Type "Urgent" in one Priority cell and "Printers" in one Category cell. Note that the spreadsheet accepts both, then undo and close without saving.
4. In Power Apps, open Tables and switch the filter to All.
5. Open the standard Account table and fill in Part B from its Columns, Relationships, Forms and Views.
6. Complete Part C: three things Dataverse gives you that tickets.csv in Excel does not.

## Check your work
- [ ] tickets.csv has 28 ticket rows (CHD-1001 to CHD-1028) and 11 columns.
- [ ] The Category column in tickets.csv holds 6 different text values: Network, Hardware, Accounts, Software, Printing, Classroom AV.
- [ ] Excel accepted "Urgent" as a priority; a Dataverse choice column would only allow Low, Medium or High.
- [ ] The Account table’s primary name column is Account Name.
