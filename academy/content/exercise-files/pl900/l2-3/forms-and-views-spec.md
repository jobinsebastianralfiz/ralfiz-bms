# Forms and views spec (Lesson 2.3)

## Main form: Ticket

Tab: General

| Section | Columns, in order |
|---|---|
| Ticket details | Title, Ticket Number, Description |
| Triage | Priority, Status, Category, Campus, Due date |

Save and publish.

## Quick create form: Ticket

Name: Ticket quick create
Columns, in order: Title, Priority, Category

Save and publish. Quick create must be allowed on the table: in the table's properties (Advanced options), make sure "Enable quick create forms" is turned on.

## Public view: Open high-priority tickets

Here "open" means any ticket that is not finished yet.

| Setting | Value |
|---|---|
| Columns | Ticket Number, Title, Priority, Status, Category, Due date |
| Filter 1 | Status Does not equal Closed |
| Filter 2 | Priority Equals High |
| Filters combined with | AND |
| Sort | Due date, ascending |

Why not "Status Equals Open"? In tickets.csv no High ticket has the status Open, so that filter would return an empty list. Try it first and see.

Save and publish.

## Test ticket (add with the quick create form)

| Column | Value |
|---|---|
| Title | Wi-Fi keeps dropping in hostel block C |
| Priority | High |
| Category | Network |

Status is not on the quick create form. It takes the default value, Open.
