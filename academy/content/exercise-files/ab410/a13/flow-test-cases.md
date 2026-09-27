# Test cases: "Notify on high priority ticket"

Trigger under test: Dataverse, When a row is added, modified or deleted
- Change type: Added or Modified. Table: Tickets. Scope: Organization
- Select columns: chd_priority
- Filter rows: chd_priority eq [numeric value of High]

Find the numeric value in the Priority column's choice list. With the chd publisher it
usually looks like 100000002 (prefix 10000 + position), but always read your own value.

Before you start, note the number of runs in the flow's run history: ____

| ID | Action in Help Desk Staff | Why | Expected |
|----|---------------------------|-----|----------|
| T1 | CHD-1025: change Priority Medium to High, save | Priority changed and matches filter | 1 new run, Succeeded |
| T2 | CHD-1017 (already High): change Title only, save | Title is not in Select columns | No run |
| T3 | CHD-1024: change Priority Low to Medium, save | Priority changed but not High | No run |
| T4 | CHD-1009 (High): change Status only, save | Status is not in Select columns | No run |
| T5 | New ticket: Title "Lab 3 PCs will not boot", Category Hardware, Priority High, Due Date 2 days from today | Added row matches filter | 1 new run, Succeeded |
| T6 | CHD-1028: change Priority Medium to High, save | Priority changed and matches filter | 1 new run, Succeeded |

Total new runs after T1 to T6: **3**

## Expected email content
| Test | Subject | Category line | Due line |
|------|---------|---------------|----------|
| T1 | High priority: Wi-Fi keeps disconnecting in the library | Category: Network | Due: 31 Aug 2026 |
| T5 | High priority: Lab 3 PCs will not boot | Category: Hardware | Due: (your date) |
| T6 | High priority: Guest Wi-Fi not working for visitors | Category: Network | Due: 03 Sep 2026 |

## What to inspect in run history (T1)
- Trigger outputs: chd_priority is the High number, not the text "High"
- Get a row by ID: the Row ID equals the trigger's _chd_category_value
- Send an email (V2): the body shows the formatted date, not 2026-08-31

## Clean-up
Set CHD-1025 and CHD-1028 back to Medium. The flow will not run for that change,
because the new value is not High.
