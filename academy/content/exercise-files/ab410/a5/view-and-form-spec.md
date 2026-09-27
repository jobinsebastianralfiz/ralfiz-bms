# A.5 spec: relationships, view and form

## Table
| Display name | Schema name | Primary column | Other columns |
|---|---|---|---|
| Ticket Comment | chd_ticketcomment | Name (text) | Comment (Multiple lines of text), Ticket (Lookup to Ticket) |

## Relationship behaviours
| Relationship | Behaviour | Why |
|---|---|---|
| Ticket (1) to Ticket Comment (N) | Parental | Comments have no meaning without their ticket; they follow it on delete, assign and share |
| Category (1) to Ticket (N) | Referential, Restrict Delete | A category that is in use must not be deleted |

Expected error when deleting Network (5 tickets use it): Dataverse blocks the delete
with a message that the record is referenced by other records.

## Public view on Ticket
| Setting | Value |
|---|---|
| Name | High priority open tickets |
| Columns | Title, Category, Due Date, Owner |
| Filter | Priority Equals High AND Status Does not equal Closed |
| Sort | Due Date ascending |

With tickets.csv loaded this view returns 1 row: CHD-1017 Laptop will not charge (Hardware, due 2026-08-20).
Change the filter to Priority Equals Medium to test it: 6 rows (CHD-1019, 1020, 1021, 1023, 1025, 1028), then set it back to High.

## Main form: Ticket
- New tab **Discussion**
  - Section Comments: subgrid, table Ticket Comment, Show related rows, view Active Ticket Comments
- General tab, next to Category: quick view control, lookup Category, quick view form showing Team and Description
  (create a quick view form on Category first if none exists)

## Delete test
1. Create a ticket: Title "Practice ticket for delete test", Category Hardware, Priority Low, Campus North.
2. Add two comments in the Discussion subgrid.
3. Ticket Comments now total 14 (12 imported + 2).
4. Delete the practice ticket. Ticket Comments return to 12.
