# Scenario: close the loop on urgent tickets

## Background
Suresh Kumar, the help desk manager, opens the Help Desk report every morning. He wants to spot urgent tickets that are not yet closed and act on them without leaving the report.

## Business rules
- An **escalation** is a ticket with Priority = High and Status not equal to Closed (Open or In progress).
- Each escalation must be posted to the Help Desk channel in Microsoft Teams so the campus lead sees it.
- Agents log and update tickets in the Power Apps Help Desk app (Dataverse) from PL-900.

## What each product does in this loop

| Need | Product | Feature you look at in this lab |
|---|---|---|
| Read the ticket data | Power BI | Dataverse connector in Get data |
| See the escalations | Power BI | Table visual with page filters |
| Post to Teams from the report | Power Automate | Power Automate visual (button that runs a flow) |
| Keep the model current | Power Automate | Power BI connector action that refreshes a semantic model (dataset) |
| React when a number crosses a line | Power Automate | Power BI trigger for a data-driven alert |
| Show a number inside an app | Power Apps | Power BI tile control in a canvas app |
| Share the report with the team | Teams | Power BI tab in a channel |

## Build (this lab)
1. A page named Escalations with a table of TicketID, Priority, Status, Campus and AssignedTo.
2. Page filters: Priority is High, Status is not Closed.
3. A Power Automate visual on the same page with TicketID in its data field.

## Flow design (optional, needs a Power Automate licence)
- Trigger: Power BI button clicked.
- For each TicketID passed from the visual: post a message in the Help Desk channel, for example "Escalation: ticket 1047 (South, Rahul) is still Open".

## Acceptance test
- The Escalations table lists exactly the unresolved High tickets and nothing else.
- Every escalation belongs to the campus shown in the table; write down which campus has them all.