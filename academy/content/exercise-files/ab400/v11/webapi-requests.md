# Web API requests (lesson D.11)

Send these from Postman or the VS Code REST Client. Replace yourorg, {tenant-id},
{client-id} and {client-secret}. Expected results assume the Ticket table holds the 28
rows of tickets.csv and the choice values listed in the D.9 test cases
(High = 100000002, Closed = 100000002). If CHD-1025 is still High from the D.10
escalation test, set it back to Medium first.

## 1. Get a token (client credentials, application user)

    POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
    Content-Type: application/x-www-form-urlencoded

    grant_type=client_credentials&client_id={client-id}&client_secret={client-secret}&scope=https://yourorg.crm.dynamics.com/.default

Expected: 200 with access_token. Paste it as {token} below. If later calls return 403,
the app has no application user or its security role cannot read chd_ticket.

## 2. Who am I?

    GET https://yourorg.crm.dynamics.com/api/data/v9.2/WhoAmI
    Authorization: Bearer {token}
    Accept: application/json

Expected: UserId is the ID of your application user, not your own user.

## 3. High priority tickets

    GET https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets?$select=chd_title,chd_duedate&$filter=chd_priority eq 100000002&$orderby=chd_duedate asc&$top=10&$count=true
    Authorization: Bearer {token}
    Accept: application/json
    OData-MaxVersion: 4.0
    OData-Version: 4.0

Expected: @odata.count = 4 (CHD-1002, CHD-1009, CHD-1014, CHD-1017).
The first row is "Account locked after failed sign-ins" (due 2026-08-06).

## 4. Same query with formatted values
Add this header to request 3:

    Prefer: odata.include-annotations="OData.Community.Display.V1.FormattedValue"

Expected: each row gains chd_duedate@OData.Community.Display.V1.FormattedValue.
Add chd_priority to $select and you also get the label "High".

## 5. Tickets that are not closed

    GET https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets?$select=chd_title&$filter=chd_status ne 100000002&$count=true
    Authorization: Bearer {token}
    Accept: application/json

Expected: @odata.count = 12 (6 Open + 6 In progress).

## 6. Count tickets per priority with $apply

    GET https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets?$apply=groupby((chd_priority),aggregate($count as total))
    Authorization: Bearer {token}
    Accept: application/json

Expected: three groups: Low 10, Medium 14, High 4.

## 7. Optimistic concurrency
Get one ticket and note its @odata.etag:

    GET https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets({ticketid})?$select=chd_title
    Authorization: Bearer {token}

Update it with a wrong ETag:

    PATCH https://yourorg.crm.dynamics.com/api/data/v9.2/chd_tickets({ticketid})
    Authorization: Bearer {token}
    Content-Type: application/json
    If-Match: W/"1"

    { "chd_title": "Title changed by the Web API" }

Expected: 412 Precondition Failed. Send it again with the real etag value: 204 No Content.
Change the title back afterwards.

## 8. Throttling
If any call returns 429 Too Many Requests, read the Retry-After header (seconds) and wait
that long before you retry. Do not retry immediately.