# Student app test plan (A.12)

Tester: ______________  Build date: ____________  Environment: CHD Dev

## Manual tests
| ID | Steps | Expected | Pass? |
|----|-------|----------|-------|
| M1 | New ticket: Title "Projector remote missing in room 110", any description, Category Classroom AV, select Submit | Green banner "Ticket saved", back on home screen | |
| M2 | New ticket: leave Title blank, select Submit | Red banner starting "Could not save:"; you stay on scrNew | |
| M3 | Same as M2 but select Quick save | Standard red error banner (from Error(FirstError) in App.OnError) | |
| M4 | After M2, read lblErrors | Shows the save error message for the Tickets table | |
| M5 | Open CHD-1025 on scrDetail, select Escalate | Banner "Escalated CHD-1025"; Priority on the ticket is now High | |

## Monitor (Advanced tools > Monitor)
| ID | Steps | Expected |
|----|-------|----------|
| MO1 | Start Monitor, repeat M1 | A network event for the Tickets data source for the create, with a duration in ms |
| MO2 | Repeat M3 with Monitor open | A Trace row with severity Error and text starting "Error:" |
| MO3 | Repeat M2 with Monitor open | No Trace row, because IfError handled the error before App.OnError |

## Test Studio (Advanced tools > Tests)
| Suite | Case | Expected result when played |
|-------|------|-----------------------------|
| Submit ticket | Valid ticket saves | Passed |
| Submit ticket | Blank title is rejected | Passed |

## Clean-up
Delete the tickets created by M1 and the Test Studio runs. Set CHD-1025 back to
Priority Medium, because later labs expect it to be Medium.
