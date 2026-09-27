# Component design worksheet - Campus Help Desk next release

Fill one row per component. Every component needs one owner, one purpose and a clear way to see failure.

## Components to design
1. chd_EscalateTicket custom API - staff, a flow and the agent must escalate a ticket the same way.
   Full spec: escalate-ticket-api-spec.md.
2. Star-rating PCF control - students rate a closed ticket 1 to 5 on the staff form and in the student canvas app.
3. Campus Directory custom connector - apps, flows and agents look up a student by email.
4. Help Desk MCP server - a Foundry agent must discover "find ticket" and "escalate ticket" tools.
5. Staff dashboard code app - React and TypeScript, lists open tickets and calls the connector.
6. Monitoring - escalation failures must alert the team.

## Design table
| # | Requirement | Component type | Reuse (where else is it used?) | Security (who can call it, how it signs in) | Monitoring (how we know it failed) |
|---|---|---|---|---|---|
| 1 | Escalate a ticket from any client | | | | |
| 2 | Clickable star rating | | | | |
| 3 | Look up a student | | | | |
| 4 | Agent discovers tools | | | | |
| 5 | Staff dashboard | | | | |
| 6 | Alert on failures | | | | |

## Inventory of the current solution
Open Campus Help Desk in make.powerapps.com and count components by type (Objects list, grouped by type):

| Type | Count | Names |
|---|---|---|
| Tables | | |
| Apps | | |
| Cloud flows | | |
| Web resources | | |
| Environment variables | | |
| Custom APIs | | |
| Other | | |

## Failure sentences
Write one sentence per component, for example:
"If chd_EscalateTicket fails, the plug-in trace log shows the exception and Application Insights raises an alert
when more than 5 failures happen in 15 minutes."

## Model answer (check after you finish)
1 Custom API, implemented by a plug-in; security via the privilege on the API or the caller's role; plug-in trace log + Application Insights.
2 PCF field component bound to a whole number column; reused in model-driven and canvas apps; errors appear in the browser console.
3 Custom connector from an OpenAPI file, OAuth 2.0 with Microsoft Entra ID; connector call failures appear in flow run history.
4 MCP server; the agent reads the tool list; its own authentication; telemetry to Application Insights.
5 Code app; Entra sign-in and sharing managed by Power Platform; Application Insights via setConfig.
6 Application Insights alerts and Power Platform monitor.
