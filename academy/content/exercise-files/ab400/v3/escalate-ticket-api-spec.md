# Spec: chd_EscalateTicket custom API

## Purpose
One message that escalates a ticket, callable from a command button, a cloud flow, the Web API and an agent.
A plug-in implements the logic (built later in the course). In this lesson you only design it and look at the form.

## Custom API record
| Field | Value |
|---|---|
| Unique name | chd_EscalateTicket |
| Display name | Escalate ticket |
| Binding type | Entity |
| Bound entity logical name | chd_ticket |
| Is function | No (it changes data, so it is an action) |
| Is private | No |
| Allowed custom processing step type | None (only your plug-in runs) |
| Plugin type | Set later, when the plug-in assembly is registered |

## Request parameter
| Unique name | Type | Optional | Description |
|---|---|---|---|
| chd_Reason | String | No | Why the ticket is escalated |

## Response property
| Unique name | Type | Description |
|---|---|---|
| NewOwnerId | Guid | The staff user who now owns the ticket |

## Behaviour
1. Read the bound ticket. If Status is Closed, throw an error "Closed tickets cannot be escalated".
2. Set Priority to High.
3. Assign the ticket to the lead of the category's team (see staff.csv for team members).
4. Return NewOwnerId.

## How it will be called (for your design table)
- Web API: POST /api/data/v9.2/chd_tickets(<ticket id>)/Microsoft.Dynamics.CRM.chd_EscalateTicket with body {"chd_Reason":"..."}
- Cloud flow: Dataverse "Perform a bound action"
- Code app: pa app add dataverse-api --api-name chd_EscalateTicket
- Agent: through a flow or connector action

## Test ticket
Use CHD-1025 "Wi-Fi keeps disconnecting in the library" (Network, Medium, Open) from tickets.csv.
After escalation it should be High priority.
