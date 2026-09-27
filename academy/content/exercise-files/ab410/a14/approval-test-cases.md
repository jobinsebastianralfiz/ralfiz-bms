# Test cases: "Approve equipment ticket"

How to get a ticket's ID: open the ticket in Help Desk Staff and copy the value after
id= in the browser address bar. To run: open the flow, select Test > Manually, and type
the TicketId when asked.

Flow outline:

    Power Apps (V2) trigger: TicketId (text)
    Scope "Try"
        Get a row by ID (Tickets, TicketId)
        Switch on the Category display name
            Case Hardware -> Start and wait for an approval (Approve/Reject - First to respond)
                             Condition Outcome = Approve
                                 yes: Update a row  Status = In progress
                                 no:  Update a row  Status = Closed, Description + comments
            Case Software -> Update a row  Status = In progress
            Default       -> Compose "Routed to general queue"
    Scope "Catch"  (run after Try: has failed, has timed out)
        Send an email (V2) with the run link and result('Try')
        Terminate  Status: Failed

| ID | Ticket | Category / Status before | What you do | Expected path | Expected result |
|----|--------|--------------------------|-------------|---------------|-----------------|
| A1 | CHD-1026 | Hardware / Open | Approve in Teams or Outlook | Hardware, yes branch | Status In progress; run Succeeded; Catch Skipped |
| A2 | CHD-1019 | Hardware / In progress | Reject with comment "Use a spare keyboard from lab 1" | Hardware, no branch | Status Closed; Description ends with the comment; run Succeeded |
| A3 | CHD-1018 | Software / In progress | Nothing | Software case | No approval sent; run Succeeded |
| A4 | CHD-1025 | Network / Open | Nothing | Default case | Compose output "Routed to general queue"; no row updated |
| A5 | 00000000-0000-0000-0000-000000000000 | (does not exist) | Nothing | Try fails at Get a row by ID | Catch runs; you receive the email; run status Failed |
| A6 | Run from A5 | | Resubmit from run history | Same as A5 | Fails again: Resubmit reuses the original trigger inputs |

## Reading run history for A5
- Try shows Failed; inside it, Get a row by ID shows the not-found error and every later action is Skipped.
- Catch shows Succeeded; Terminate shows the Failed status you configured.
- In the email, find the item whose status is Failed in the result('Try') text.

## Clean-up
Set CHD-1026 back to Open and CHD-1019 back to In progress, and remove the added comment
from the CHD-1019 description.
