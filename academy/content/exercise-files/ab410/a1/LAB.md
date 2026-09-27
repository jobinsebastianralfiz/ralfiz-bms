# AB-410 · A.1 From PL-900 to AB-410

## Files
- shared-data/hd/categories.csv
- shared-data/hd/tickets.csv
- setup-checklist.md

## Steps
1. Download the exercise files for this lab and open setup-checklist.md next to the browser.
2. Sign up for the Power Apps Developer Plan and create two developer environments with a Dataverse database: CHD Dev and CHD Test. Write both URLs in setup-checklist.md.
3. In CHD Dev, open Solutions and create the publisher Campus Help Desk with prefix chd. Write the generated choice value prefix in the checklist.
4. Create the solution Campus Help Desk (name CampusHelpDesk) with that publisher and set it as the preferred solution.
5. Add your PL-900 Ticket and Category tables with Add existing, or create them inside the solution using the column tables in section 3 of setup-checklist.md.
6. Open the Category table and choose Import > Import data from Excel or CSV. Import categories.csv first, mapping Name, Team and Description.
7. Import tickets.csv into Ticket the same way. Map Title, Description, Priority, Status, Campus, Student Email, Assigned To, the two dates and Category (matched on the category Name).
8. Export the solution once unmanaged and once managed, then import the managed zip into CHD Test and play the Help Desk Staff app there.
9. Open the AB-410 study guide and copy its skill bullets into section 6 of the checklist.

## Check your work
- [ ] The Category table shows 6 rows: Network, Hardware, Accounts, Software, Printing and Classroom AV.
- [ ] The Ticket table shows 28 rows, CHD-1001 to CHD-1028.
- [ ] Filtering Ticket on Priority gives 4 High, 14 Medium and 10 Low; on Status gives 16 Closed, 6 In progress and 6 Open.
- [ ] The Ticket table’s schema name is chd_ticket and its columns start with chd_.
- [ ] In CHD Test, Solutions lists Campus Help Desk with Managed = Yes (the managed import brings components, not the 28 data rows).
