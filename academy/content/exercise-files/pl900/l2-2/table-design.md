# Table design: Category and Ticket (Lesson 2.2)

Build these two tables in your developer environment, then load the data from categories.csv and tickets.csv.

## Table 1: Category

| Display name | Data type | Notes |
|---|---|---|
| Name | Single line of text | Primary name column |
| Team | Single line of text | |
| Description | Multiple lines of text | |

Plural name: Categories. Rows to load: categories.csv (6 rows).

## Table 2: Ticket

| Display name | Data type | Notes |
|---|---|---|
| Title | Single line of text | Primary name column |
| Ticket Number | Single line of text | e.g. CHD-1001 |
| Description | Multiple lines of text | |
| Category | Lookup | Points to Category |
| Priority | Choice | Low, Medium, High |
| Status | Choice | Open, In progress, Closed. Default value: Open |
| Campus | Choice | North, South, City |
| Due date | Date only | |

Plural name: Tickets. Rows to load: tickets.csv (28 rows).

Set the Status default to Open. Lesson 2.3 relies on new tickets starting as Open.

## Relationship

One Category has many Tickets (1:N). Seen from Ticket, it is many-to-one (N:1).
The lookup column lives on the "many" side: Ticket.

## CSV to column mapping for tickets.csv

| CSV column | Ticket column |
|---|---|
| Ticket Number | Ticket Number |
| Title | Title |
| Description | Description |
| Category | Category (lookup, matched on the Category Name) |
| Priority | Priority |
| Status | Status |
| Campus | Campus |
| Due Date | Due date |
| Student Email | Ignore (not needed yet) |
| Assigned To | Ignore (not needed yet) |
| Created On | Ignore (Dataverse sets its own Created On) |

Load Category first. A ticket's Category lookup can only match a category row that already exists.

## If the import will not map a column

Import tools differ. If a choice or lookup column refuses to map, import the text columns first, then use Edit data to set the missing values on a few rows, or add five tickets by hand as the original lab describes.
