# AB-410 · A.5 Relationships, views and main forms

## Files
- ticket-comments.csv
- view-and-form-spec.md
- shared-data/hd/tickets.csv

## Steps
1. Download the exercise files and open view-and-form-spec.md.
2. Create the Ticket Comment table (chd_ticketcomment) with a Comment column and a Ticket lookup. Set the Ticket relationship behaviour to Parental.
3. Open Ticket Comments in Help Desk Staff and import ticket-comments.csv, mapping Name, Comment and Ticket (the Ticket column holds the ticket Title). Skip Ticket Number.
4. Set the Category-to-Ticket relationship to Referential, Restrict Delete, then try to delete the Network category in Help Desk Staff and read the error.
5. Switch that relationship to Custom, review each action, and set it back to Referential, Restrict Delete.
6. Create the public view High priority open tickets exactly as in view-and-form-spec.md. Save and publish.
7. Add the Discussion tab with a Ticket Comment subgrid and a Category quick view control to the Ticket main form. Save and publish.
8. Run the delete test at the bottom of view-and-form-spec.md: create the practice ticket, add two comments, then delete the ticket.

## Check your work
- [ ] Ticket Comments shows 12 rows after the import; CHD-1017 Laptop will not charge shows 3 of them in its Discussion subgrid.
- [ ] Deleting the Network category is blocked because 5 tickets use it.
- [ ] High priority open tickets returns 1 row: CHD-1017, due 2026-08-20.
- [ ] After deleting the practice ticket, the Ticket Comments count goes from 14 back to 12.
