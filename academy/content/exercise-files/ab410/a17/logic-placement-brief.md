# Logic placement brief (A.17)

From: Suresh Kumar, Help desk manager
To: Campus Help Desk makers

We keep finding rules that work in one app but not another. For each requirement below,
choose where it should live and write one line of reasoning. Options: Business rule
(say which scope), Formula column, Rollup column, Business process flow, Cloud flow,
Power Fx in the canvas app. Items marked BUILD must be built in this lab.

| # | Requirement | Your choice | Reason |
|---|-------------|-------------|--------|
| R1 | BUILD. A High priority ticket must have a Due Date, whether it is created in the staff app, the student app, by import or by a flow. | | |
| R2 | BUILD. Each ticket shows how many days it has been open. Closed tickets show nothing. Always current when a row is opened. | | |
| R3 | BUILD. Each Category shows how many of its tickets have Status Open. A delay of an hour is fine. | | |
| R4 | BUILD. Staff follow New, Assigned, Resolved, Closed for every ticket and cannot reach Closed without a resolution. | | |
| R5 | When a ticket is closed, email the student a link to the feedback form. | | |
| R6 | In the student app, the Submit button stays disabled until the description has at least 20 characters. | | |
| R7 | On the staff form, lock Description once Status is Closed. | | |
| R8 | Every Monday at 08:00, post the number of overdue tickets to the Teams channel. | | |

## Build details

R1 business rule on Ticket, name "High priority needs due date", scope Entity:

    IF   Priority equals High
    AND  Due Date does not contain data
    THEN Show error message on Due Date:
         "High priority tickets need a due date."

R2 formula column on Ticket: see formula-column.txt.

R3 rollup column on Category, name Open Tickets (chd_opentickets), Whole number:
- Related entity: Tickets (Category)
- Filter: Status equals Open
- Aggregation: Count of Ticket

R4 business process flow "Ticket lifecycle" on Ticket:

| Stage | Data steps | Required |
|-------|-----------|----------|
| New | Category, Priority | Category |
| Assigned | Owner | Owner |
| Resolved | Resolution Notes | Resolution Notes |
| Closed | Resolved On | No |

## Expected results with tickets.csv
Rollup Open Tickets after refresh:

| Category | Open Tickets |
|----------|--------------|
| Accounts | 1 |
| Classroom AV | 1 |
| Hardware | 1 |
| Network | 2 |
| Printing | 1 |
| Software | 0 |

Days open: 16 Closed tickets show an empty value; the other 12 show a whole number.
Add any tickets you created in earlier labs to these numbers.
