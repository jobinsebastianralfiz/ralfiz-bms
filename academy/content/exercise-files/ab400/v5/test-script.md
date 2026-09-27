# Test script - ticket.js on the Ticket main form

## Prepare the data (once)
1. Import tickets.csv into the Ticket table (28 rows) if you have not already.
2. In the Active Tickets view, filter Status = Closed. You should see 16 rows.
3. Select all 16 and choose Deactivate. They move to Inactive (statecode 1). The script counts only active rows (statecode eq 0).
4. 12 tickets stay active. Per category: Network 3, Hardware 3, Accounts 2, Classroom AV 2, Software 1, Printing 1.

## Tests
| # | Steps | Expected result |
|---|---|---|
| T1 | Open CHD-1025 (Network, Medium). | No notification. Due date is not required. |
| T2 | Change Priority to High. | Yellow bar "High priority: set a Due date." Due date shows a red asterisk. Alert: "3 open tickets in Network." |
| T3 | Change Priority back to Medium. | The notification disappears and Due date is optional again. |
| T4 | Open CHD-1017 (Hardware, High). | Warning bar on load and alert "3 open tickets in Hardware." |
| T5 | Open CHD-1027 (Printing, Low), set Priority to High. | Alert "1 open tickets in Printing." |
| T6 | Press F12 > Sources, find ticket.js, set a breakpoint in onPriorityChange, change Priority. | Execution stops on your breakpoint; formContext is defined. |
| T7 | Select the new "Close ticket" command on an open ticket. | Status becomes Closed. The button is hidden on a ticket that is already Closed. |

## If something fails
- "executionContext is undefined": you did not tick Pass execution context as first parameter.
- Nothing happens on change: check the HIGH value against your chd_priority choice values.
- Alert shows 0: the lookup column may have a different schema name; check _chd_category_value in the Web API.

## Close ticket command (Power Fx)
Action:     Patch(Tickets, Self.Selected.Item, { Status: 'Status (Tickets)'.Closed })
Visible:    Self.Selected.Item.Status <> 'Status (Tickets)'.Closed
Replace the table and choice names with the display names in your environment.
