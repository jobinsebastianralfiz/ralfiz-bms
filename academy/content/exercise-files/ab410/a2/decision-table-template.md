# Decision table

| Id | Chosen component | Reason | Extensibility needed? |
|---|---|---|---|
| R1 | | | |
| R2 | | | |
| R3 | | | |
| R4 | | | |
| R5 | | | |
| R6 | | | |
| R7 | | | |
| R8 | | | |
| R9 | | | |
| R10 | | | |
| R11 | | | |
| R12 | | | |

| Stage | Environment type | Reason |
|---|---|---|
| Development | | |
| Test | | |
| Production | | |

Requirements Plan designer missed (write at least three):
1.
2.
3.

---

## Model answer (read only after you finish)

| Id | Component | Reason | Extensibility |
|---|---|---|---|
| R1 | Dataverse tables Ticket, Category; standard Contact for students | Relational data, security by business unit | No |
| R2 | Canvas app (phone layout) | Task-focused mobile screens | No |
| R3 | Model-driven app Help Desk Staff | Views, forms, many related records | No |
| R4 | Automated cloud flow (Office 365 Outlook: When a new email arrives) | Runs without a person on an event | No |
| R5 | Prompt column on Ticket (stored) or row summary (shown on form) | Summarise text; column if reports need it | No |
| R6 | Prompt column or AI Hub prompt called from a flow | Classify text into one of six categories | No |
| R7 | Scheduled cloud flow | Runs on a timer, compares Due Date with now | No |
| R8 | Copilot Studio agent with the IT FAQ as knowledge | Chat at any hour | No |
| R9 | Power Pages site with a basic form | External, anonymous users | No |
| R10 | Business units + security roles (Read Business Unit for agents) | Row access follows campus | No |
| R11 | Scheduled cloud flow + AI Hub prompt for the summary | Weekly timer, generated text | No |
| R12 | Custom connector from the OpenAPI file | No built-in connector exists | Yes: custom connector |

| Stage | Type | Reason |
|---|---|---|
| Development | Developer | Personal, free, one maker |
| Test | Sandbox | Can be reset and copied; not for live use |
| Production | Production | Full support, backups, for live users |
