# Campus Help Desk: Power BI data dictionary

You use two files through the whole PL-300 track. Save both in one folder, for example Documents\HelpDesk.

## tickets.csv (fact table, 60 rows)

| Column | Type in Power BI | Meaning |
|---|---|---|
| TicketID | Whole number | Unique ticket number, 1001 to 1060 |
| CreatedDate | Date | Day the ticket was logged (January to June 2026) |
| ClosedDate | Date | Day the ticket was closed. Empty while the ticket is Open or In progress |
| CategoryID | Whole number | Key to categories.csv (1 to 4) |
| Priority | Text | Low, Medium or High |
| Status | Text | Open, In progress or Closed |
| HoursToResolve | Decimal number | Working hours from creation to closure. Empty until closed |
| Campus | Text | North, South or City |
| AssignedTo | Text | Agent first name: Anu, Rahul, Meera or Joseph |

## categories.csv (dimension table, 4 rows)

| Column | Type | Meaning |
|---|---|---|
| CategoryID | Whole number | Unique key, 1 to 4 |
| Name | Text | Network, Hardware, Accounts, Software |
| Team | Text | Infrastructure, Identity or Applications |

## How the tables relate

- One category has many tickets: categories[CategoryID] (one) to tickets[CategoryID] (many).
- Later lessons add a Date table (B.6) and a Staff table (B.15).

## Data quality warning

This export comes from a help desk tool that lets agents type values freely. Some rows do not follow the rules in the table above. Do not fix anything by hand in the CSV: in lesson B.4 you find and fix the problems in Power Query, so the fix repeats on every refresh.

## Agents

| AssignedTo | Full name | Email |
|---|---|---|
| Anu | Anu Sebastian | anu.sebastian@staff.example.edu |
| Rahul | Rahul Varma | rahul.varma@staff.example.edu |
| Meera | Meera Iyer | meera.iyer@staff.example.edu |
| Joseph | Joseph Mathew | joseph.mathew@staff.example.edu |