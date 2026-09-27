# Campus Help Desk: requirements brief (v2)

## Background
The college runs three campuses: North, South and City. Students report IT and
facilities problems. Six staff work on the help desk (see staff.csv): four agents,
one team lead and one manager. Last term there were 28 tickets in five weeks
(tickets.csv), and the college expects volume to triple after the new hostel opens.

## Roles
- **Student**: reports problems, checks status, rates the fix.
- **Help desk agent**: triages, works on and closes tickets for their campus.
- **Team lead**: reassigns work across agents, watches due dates.
- **Help desk manager**: sees all campuses, needs weekly numbers.
- **Visitor**: seminar guests who need Wi-Fi help (no college account).

## Requirements
| Id | Requirement |
|---|---|
| R1 | Store tickets with category, priority, status, campus, student and due date. Categories are the six in categories.csv. |
| R2 | Students report a ticket from their phone in under a minute. |
| R3 | Agents work in a list-and-form screen with views such as My open tickets. |
| R4 | Tickets sent to helpdesk@college.example.edu become tickets automatically. |
| R5 | Agents see a one-line summary of long descriptions without reading them. |
| R6 | The system suggests a category for new tickets. |
| R7 | Warn the assigned agent 24 hours before a ticket is due. |
| R8 | Students ask common questions (Wi-Fi, VPN, passwords, printing) in chat at any hour. |
| R9 | Visitors without an account can submit a Wi-Fi problem on a public web page. |
| R10 | Agents only see tickets for their own campus; managers see all. |
| R11 | Every Monday at 8 am, managers get a summary of last week’s tickets. |
| R12 | The college’s asset system (REST API, OpenAPI file available) must be looked up from a ticket to show the laptop’s warranty. |

## Constraints
- Build in a developer environment, test in a second environment, then go live.
- Keep everything in the Campus Help Desk solution (prefix chd).
- Prefer low-code. Use code only when a requirement cannot be met otherwise.

## Your task
Fill decision-table-template.md: one row per requirement with the component,
the reason and any extensibility. Then recommend an environment type for
development, test and production.
