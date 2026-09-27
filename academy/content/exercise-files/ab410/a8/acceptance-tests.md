# Acceptance tests: Help Desk Staff

## As yourself (System Administrator)
| # | Check | Expected |
|---|---|---|
| 1 | Left navigation | Two groups: Work (Tickets, Ticket Comments) and Setup (Categories) |
| 2 | Tickets view selector, system views | Exactly 3: Active Tickets, High priority open tickets, My Open Tickets |
| 3 | High priority open tickets | 1 row: CHD-1017 |
| 4 | Open any ticket | Opens on Ticket - Manager (first form you have a role for) |
| 5 | Categories | 6 rows |

## As the test user (Help Desk Agent, North Campus, member of IT Support North)
| # | Check | Expected |
|---|---|---|
| 6 | Open the app from make.powerapps.com or the app URL | Opens without an access error |
| 7 | Open CHD-1019 | Form name is Ticket; the form selector does not list Ticket - Manager |
| 8 | Active Tickets | The 4 IT Support North tickets (CHD-1019, CHD-1021, CHD-1024, CHD-1027) plus the ticket the test user created in A.7 test 7: 5 rows |
| 9 | Views list | Same 3 system views; the user may add personal views |
| 10 | Setup group | Categories opens read-only list of 6 rows |

## If something fails
- App will not open: the role is not assigned to the app (Share, then add the role).
- Wrong form: check form order and the form’s security roles.
- Extra views: a view is still selected in the Tickets page settings; clear it and publish.
