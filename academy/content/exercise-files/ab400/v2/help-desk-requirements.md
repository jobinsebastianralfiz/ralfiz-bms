# Campus Help Desk - release 2 requirements

From: Help Desk manager. To: developer.
Dataverse tables already exist in the Campus Help Desk solution (prefix chd): Ticket (chd_ticket), Category.
Load the data from tickets.csv (28 tickets) and categories.csv (6 categories) if you have not already.

| ID | Requirement | Notes from the business |
|---|---|---|
| R1 | Make Due date required when Priority is High, on the form. | Makers maintain this; no developer should be needed to change it. |
| R2 | When staff change Category on the form, show how many open tickets that category already has. | Only on the staff form. It must be instant. |
| R3 | Block saving any ticket whose Title contains banned words. | Tickets arrive from the canvas app, the staff app, imports and the Web API. All must be blocked. |
| R4 | Every night, check open tickets against their Due date and mark SLA breaches. | The job reads thousands of rows. |
| R5 | When a ticket closes, email the student and post in the staff Teams channel. | Uses Outlook and Teams. |
| R6 | Students ask in plain language how to reset their Wi-Fi password. | Answers come from the IT FAQ (pl900/l5-3/it-faq.md). |
| R7 | After a ticket is created, look up the student's department in the Campus Directory API. | The user must not wait for the call. |
| R8 | A new High priority ticket needs manager approval before it is assigned. | The manager approves from Outlook or Teams. |

## Constraints
- Prefer out-of-the-box features. Code is the last resort.
- Deterministic rules (deadlines, banned words) must give the same result every time: no AI for them.
- Student records stay in the Campus Directory. Do not copy them into Dataverse.

## Environment facts to record (from the Power Platform admin center)
- Environment name and type (Developer, Sandbox, Production)
- Managed environment: Yes / No
- Data policies that apply, and whether Office 365 Outlook, Microsoft Teams and HTTP are in the same group
- Security roles you hold

Write your answers in architecture-decision-brief.md.
