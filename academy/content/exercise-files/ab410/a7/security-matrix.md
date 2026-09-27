# A.7 security matrix

## Business units
| Business unit | Parent | Who sits here |
|---|---|---|
| (root, your org name) | none | Suresh Kumar (manager), you |
| North Campus | root | Anu Sebastian, Joseph Mathew, test user |
| City Campus | root | Meera Iyer, Divya Nair |

South Campus is left out on purpose to keep the lab short; South tickets stay with the root unit.

## Security roles
Help Desk Agent (copy of Basic User)
| Table | Create | Read | Write | Delete | Append | Append To | Assign | Share |
|---|---|---|---|---|---|---|---|---|
| Ticket | User | Business Unit | User | None | Business Unit | Business Unit | None | User |
| Ticket Comment | User | Business Unit | User | User | Business Unit | Business Unit | None | None |
| Category | None | Organization | None | None | None | Organization | None | None |

Help Desk Manager (copy of Basic User, used in A.8)
| Table | Create | Read | Write | Delete | Append | Append To | Assign | Share |
|---|---|---|---|---|---|---|---|---|
| Ticket | Parent: Child | Parent: Child | Parent: Child | None | Parent: Child | Parent: Child | Parent: Child | Parent: Child |
| Category | Organization | Organization | Organization | None | Organization | Organization | None | None |

## Owner team
| Team | Business unit | Role | Members |
|---|---|---|---|
| IT Support North | North Campus | Help Desk Agent | test user |

Assign these four open or in-progress North tickets to IT Support North:
| Ticket | Title | Status |
|---|---|---|
| CHD-1019 | Keyboard keys not working | In progress |
| CHD-1021 | No sound from classroom speakers | In progress |
| CHD-1024 | Lecture capture did not record | Open |
| CHD-1027 | Print credits not added | Open |

## Column security
| Column | Table | Profile | Read | Update | Create | Members |
|---|---|---|---|---|---|---|
| Internal notes (chd_internalnotes) | Ticket | Help Desk Leads | Yes | Yes | No | you only |

Put this text in Internal notes on CHD-1019: "Second keyboard fault in lab 4 this term. Check for liquid damage."

## Sharing
| Ticket | Share with | Rights |
|---|---|---|
| CHD-1023 Forgot my password (City) | a user in City Campus | Read |
