# AB-410 · A.4 Tables and columns in depth

## Files
- column-spec.md
- contacts-import.csv
- shared-data/hd/students.csv

## Steps
1. Download the exercise files and open column-spec.md.
2. In the Campus Help Desk solution, open Ticket and add Ticket Number as an Autonumber column with prefix CHD-, 4 digits and seed 1029, as in column-spec.md.
3. Add Channel as a choice synced with a new global choice chd_channel (Web, Email, Walk-in).
4. Add Resolved On (Date only, behaviour Date only), Resolution Notes (Multiple lines of text) and Screenshot (Image). Turn on Audit changes in the table properties.
5. Open the standard Contact table and add the text column Student ID (chd_studentid).
6. Import contacts-import.csv into Contact with Import > Import data from Excel or CSV, mapping the columns as in column-spec.md.
7. Create one new ticket in Help Desk Staff and note its Ticket Number.
8. Open the data workspace, add Ticket, Category and Contact, and look at the relationships between them.

## Check your work
- [ ] The new test ticket gets Ticket Number CHD-1029, continuing after the last ticket in tickets.csv.
- [ ] The Contact table has 20 rows with a Student ID, S2026101 to S2026120 (7 North, 7 South, 6 City).
- [ ] Channel appears under Choices in the solution as the global choice chd_channel with 3 values.
- [ ] Resolved On shows behaviour Date only in the column’s advanced options, and Ticket shows Audit changes turned on.
- [ ] The data workspace shows a many-to-one relationship from Ticket to Category.
