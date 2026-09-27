# Help Desk Staff: app map

## Navigation
| Area | Group | Subarea (page) | Type |
|---|---|---|---|
| Area 1 | Work | Tickets | Dataverse table (chd_ticket) |
| Area 1 | Work | Ticket Comments | Dataverse table (chd_ticketcomment) |
| Area 1 | Setup | Categories | Dataverse table (chd_category) |

Order inside Work: Tickets first, then Ticket Comments.

## Forms for Tickets
| Form | Type | Order | Security roles |
|---|---|---|---|
| Ticket - Manager | Main | 1 | Help Desk Manager, System Administrator |
| Ticket | Main | 2 (fallback form) | Everyone |
| Ticket Quick Create | Quick create | n/a | Everyone |

Ticket - Manager is a copy of Ticket (use Save as) with an extra section SLA
showing Due Date, Resolved On, Owner and Internal notes.

## Views for Tickets (include only these)
| View | Filter | Rows with tickets.csv (as admin) |
|---|---|---|
| Active Tickets | State is Active | 28, plus any tickets you created in earlier labs |
| My Open Tickets | Owner is current user AND Status is not Closed | depends on who you are |
| High priority open tickets | Priority is High AND Status is not Closed | 1 |

Create My Open Tickets if it does not exist (copy Active Tickets with Save as,
then edit the filter).

## App access
| Role | Assigned to app | Default form they see |
|---|---|---|
| Help Desk Agent | Yes | Ticket |
| Help Desk Manager | Yes | Ticket - Manager |
| System Administrator | always | Ticket - Manager |
