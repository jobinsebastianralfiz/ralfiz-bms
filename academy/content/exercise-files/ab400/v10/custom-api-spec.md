# Custom API and business event spec (lesson D.10)

Create everything inside the **Campus Help Desk** solution (publisher prefix chd).
This is the version you build in D.10. The D.3 design sketch returned NewOwnerId; this
lab follows the lesson and returns the new priority. The rule "Closed tickets cannot be
escalated" from D.3 stays.

## 0. Column to add first
| Table | Display name | Logical name | Type | Max length |
|---|---|---|---|---|
| Ticket | Escalation reason | chd_escalationreason | Text (single line) | 200 |

## 1. Custom API: chd_EscalateTicket
| Property | Value |
|---|---|
| Unique name | chd_EscalateTicket |
| Display name | Escalate ticket |
| Binding type | Entity |
| Bound entity logical name | chd_ticket |
| Is function | No (an action, called with POST) |
| Is private | No |
| Allowed custom processing step type | None |
| Plugin Type | ChdPlugins.EscalateTicket (set after you update the assembly) |

Request parameter

| Unique name | Display name | Type | Is optional |
|---|---|---|---|
| chd_Reason | Reason | String | No |

Response property

| Unique name | Display name | Type |
|---|---|---|
| chd_NewPriority | New priority | Integer |

## 2. Business event: chd_TicketResolved
| Property | Value |
|---|---|
| Unique name | chd_TicketResolved |
| Binding type | Global |
| Is function | No |
| Allowed custom processing step type | Async Only |
| Plugin Type | (empty) |
| Response properties | (none) |

Request parameter: chd_TicketId, type Guid, not optional.

Catalog: a root catalog **Help Desk events** with a child catalog (category) **Tickets**,
and a catalog assignment that points to chd_TicketResolved. Add all three to the solution.

## 3. Test requests
Replace yourorg with your environment and send the requests from Postman or the
VS Code REST Client with a bearer token (see lesson D.11 for getting a token).

### 3.1 Find the ID of CHD-1025

    GET https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets?$select=chd_ticketid,chd_title,chd_priority&$filter=chd_title eq 'Wi-Fi keeps disconnecting in the library'
    Authorization: Bearer {token}
    Accept: application/json

Expected: one row, chd_priority = 100000001 (Medium).

### 3.2 Escalate it

    POST https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets({ticketid})/Microsoft.Dynamics.CRM.chd_EscalateTicket
    Authorization: Bearer {token}
    Content-Type: application/json

    { "chd_Reason": "Several students in the library cannot work" }

Expected: 200 OK with a body like

    {
      "@odata.context": "https://yourorg.crm.dynamics.com/api/data/v9.2/$metadata#Microsoft.Dynamics.CRM.chd_EscalateTicketResponse",
      "chd_NewPriority": 100000002
    }

### 3.3 Send an empty reason

    POST https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets({ticketid})/Microsoft.Dynamics.CRM.chd_EscalateTicket
    Authorization: Bearer {token}
    Content-Type: application/json

    { "chd_Reason": "   " }

Expected: an error response whose message is "Please give a reason for escalation."
and no change to the ticket.

### 3.4 Raise the business event

    POST https://yourorg.crm.dynamics.com/api/data/v9.2/chd_TicketResolved
    Authorization: Bearer {token}
    Content-Type: application/json

    { "chd_TicketId": "{ticketid}" }

Expected: 204 No Content (a business event has no response properties). A flow that
uses **When an action is performed** with catalog Help Desk events, category Tickets and
action chd_TicketResolved starts a new run within a few minutes.

### 3.5 Try to escalate a closed ticket
Find the ID of CHD-1001 "Printer out of toner in library" (Closed) as in 3.1 and send
request 3.2 for it.
Expected: an error with the message "Closed tickets cannot be escalated." and CHD-1001
keeps Priority Medium.

## 4. Acceptance criteria
- The custom API row shows Plugin Type ChdPlugins.EscalateTicket; no step is registered for it.
- After 3.2, CHD-1025 shows Priority High and Escalation reason "Several students in the library cannot work".
- 3.3 returns the friendly error and leaves the Escalation reason unchanged.
- 3.5 is refused for the closed ticket CHD-1001.
- chd_TicketResolved appears under your catalog in the flow trigger, and 3.4 starts the flow.