# PL-900 · 2.2 Tables, columns and relationships

## Files
- shared-data/hd/categories.csv
- shared-data/hd/tickets.csv
- table-design.md

## Steps
1. Download categories.csv, tickets.csv and table-design.md.
2. Create the Category table with the Name, Team and Description columns from table-design.md.
3. Load categories.csv into Category: open the table and choose Import > Import data from Excel or CSV (or add the rows with Edit data).
4. Create the Ticket table with every column in table-design.md: Title as the primary name, Priority, Status and Campus as choices, and Status defaulting to Open.
5. On Ticket, add the lookup column Category pointing to the Category table.
6. Open the Relationships tab on Ticket and confirm the many-to-one link to Category.
7. Import tickets.csv into Ticket, using the CSV-to-column mapping in table-design.md and ignoring Student Email, Assigned To and Created On.
8. Open Edit data on Ticket and spot-check CHD-1001: Printing category, Medium priority, Closed status, North campus.

## Check your work
- [ ] The Category table has 6 rows.
- [ ] The Ticket table has 28 rows.
- [ ] Filtering Ticket by Priority = High shows 4 rows: CHD-1002, CHD-1009, CHD-1014 and CHD-1017.
- [ ] Opening the Accounts category’s related tickets shows 5 tickets; Printing shows 4.
- [ ] The Relationships tab on Ticket lists a many-to-one relationship to Category.
