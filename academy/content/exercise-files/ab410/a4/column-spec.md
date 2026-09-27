# Column spec for A.4

## Ticket (chd_ticket): new columns
| Display name | Schema name | Type | Settings |
|---|---|---|---|
| Ticket Number | chd_ticketnumber | Autonumber | String prefixed number, prefix CHD-, minimum digits 4, seed 1029 |
| Channel | chd_channel | Choice | Sync with global choice chd_channel: Web, Email, Walk-in; default Web |
| Resolved On | chd_resolvedon | Date only | Behaviour: Date only |
| Resolution Notes | chd_resolutionnotes | Multiple lines of text | Max 4,000 characters |
| Screenshot | chd_screenshot | Image | Can store full images: off |

If Ticket Number already exists as text from A.1, delete it first (or name the new
column Ticket No) because a column’s data type cannot be changed to Autonumber.
The seed 1029 makes the first new ticket continue after CHD-1028 in tickets.csv.

## Ticket: table properties
| Property | Value |
|---|---|
| Audit changes to its data | On |
| Ownership | User or team (already set; cannot change) |

## Contact (standard table): new column
| Display name | Schema name | Type |
|---|---|---|
| Student ID | chd_studentid | Single line of text, 20 characters |

Import contacts-import.csv into Contact. Map:
| CSV column | Contact column |
|---|---|
| First Name | First Name |
| Last Name | Last Name |
| Email | Email |
| Student ID | Student ID |
| Campus | (skip, or map to Address 1: City if you want to keep it) |

## Why these types
- Date only behaviour: a due or resolved date must not shift when users in other time zones open it.
- Global choice: Channel will be reused on the Ticket Comment table later.
- Contact, not a new Student table: Contact already works with email, activities and portals.
