# Model answers - architecture decision brief

| ID | Component | Why |
|---|---|---|
| R1 | Business rule | Show, hide, require and set-value on a form is exactly what business rules do, with no code and maintained by makers. |
| R2 | Client script (JavaScript) | Form-only, instant feedback that needs Xrm.WebApi and a notification. Built in lesson D.5 (v5). |
| R3 | Synchronous plug-in | Only server-side logic inside the transaction runs for every channel and can cancel the save with an error. |
| R4 | Asynchronous plug-in or Azure Function | Heavy, scheduled work belongs outside the user transaction: an Azure Function with a timer trigger. |
| R5 | Cloud flow | Notifications through Outlook and Teams with standard connectors, triggered when Status changes to Closed. |
| R6 | Copilot Studio agent | Conversational, knowledge-grounded answers from the IT FAQ. |
| R7 | Asynchronous plug-in or Azure Function | An external call that can run after the save, so the user does not wait. |
| R8 | Cloud flow | Approvals are built into cloud flows with the Approvals connector. |

Totals: Business rule 1, Client script 1, Synchronous plug-in 1, Asynchronous plug-in or Azure Function 2, Cloud flow 2, Copilot Studio agent 1.

## Out-of-the-box check
Only R1 can be met by a business rule alone. R3 looks like validation, but "contains banned words" from
every channel, including the Web API, needs a synchronous plug-in.

## Data decision
Connector (custom connector to the Campus Directory API), or a virtual table if staff must see directory
rows in views. Not a standard table: the data must stay in the directory.

## Deterministic vs AI
R3 and R4 are fixed rules and must not use prompts or agents. Only R6 uses AI, and its answers may vary.

## Three layers
- User experience: staff model-driven app (form with business rule + client script), student canvas app, agent chat.
- Logic: business rule, client script, synchronous plug-in, asynchronous plug-in, Azure Function, cloud flows, agent.
- Data: Dataverse (Ticket, Category), Campus Directory API via connector.
