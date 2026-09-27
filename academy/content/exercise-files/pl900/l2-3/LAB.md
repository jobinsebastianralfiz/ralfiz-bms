# PL-900 · 2.3 Forms and views

## Files
- forms-and-views-spec.md

## Steps
1. Download forms-and-views-spec.md.
2. Edit the Ticket main form: add the two sections Ticket details and Triage with the columns listed in the spec. Save and publish.
3. Create the quick create form with only Title, Priority and Category. Check that quick create forms are enabled on the table. Save and publish.
4. Create the public view with Status = Open and Priority = High first, and note how many rows it shows.
5. Change the Status filter to "Does not equal Closed", set the columns and sort by Due date ascending, and name it "Open high-priority tickets". Save and publish.
6. Use the quick create form to add the test ticket from the spec (Wi-Fi keeps dropping in hostel block C, High, Network).
7. Open the "Open high-priority tickets" view again and compare the rows.

## Check your work
- [ ] With Status Equals Open and Priority Equals High, the view shows 0 rows: no High ticket in tickets.csv is Open.
- [ ] With Status Does not equal Closed, the view shows 1 row: CHD-1017 "Laptop will not charge" (In progress, due 2026-08-20).
- [ ] After adding the quick create ticket, the view shows 2 rows, and the new ticket’s Status is Open.
- [ ] The Active Tickets view now lists 29 tickets.
- [ ] The main form shows Priority, Status, Category, Campus and Due date together in the Triage section.
