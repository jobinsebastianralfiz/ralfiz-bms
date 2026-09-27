# Help Desk Staff: model-driven app spec (Lesson 3.2)

## Users
Help desk agents and the help desk manager (see **staff.csv**). They work at a desk on a large screen
and need to triage, update and close tickets quickly.

## Navigation (site map)
| Area | Group | Page | Type |
|------|-------|------|------|
| Help desk | Work | Tickets | Dataverse table: Ticket |
| Help desk | Setup | Categories | Dataverse table: Category |
| Help desk | Insights | Tickets by priority | Chart on the Ticket views (optional) |

## Components to include
- Ticket **main form** from Lesson 2.3 (two sections: Details, Tracking).
- Ticket **quick create form** (Title, Priority, Category).
- Ticket views: **Active Tickets** (default) and **Open high-priority tickets**.
- Category main form and Active Categories view.
- Optional chart: **Tickets by Priority** (column chart, count of Title grouped by Priority).

## Settings to check
- Quick create must be enabled on the Ticket table (table properties: "Enable quick create forms").
- The app name is exactly **Help Desk Staff**.

## Acceptance tests
| # | Test | Expected (with the 28 rows of tickets.csv) |
|---|------|---------------------------------------------|
| 1 | Open Tickets page, Active Tickets view | 28 rows |
| 2 | Switch to Open high-priority tickets | 0 rows (no ticket in the file is both Open and High) |
| 3 | From Categories, open Hardware, add a related Ticket with quick create: Title "Tablet screen cracked", Priority High, Status Open | Quick create panel opens on the right; the ticket saves |
| 4 | Go back to Open high-priority tickets | 1 row: Tablet screen cracked |
| 5 | Show the Tickets by Priority chart on Active Tickets | Medium 14, Low 10, High 5 (4 from the file plus your new one) |
