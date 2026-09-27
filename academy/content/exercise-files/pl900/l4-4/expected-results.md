# Expected results (Lesson 4.4)

Based on the 28 rows of **tickets.csv**. Add any Open tickets you created in earlier labs.

## Before Prompt 2 (Status = Open)
List rows returns **6** rows:

| Ticket | Title | Priority |
|--------|-------|----------|
| CHD-1023 | Forgot my password | Medium |
| CHD-1024 | Lecture capture did not record | Low |
| CHD-1025 | Wi-Fi keeps disconnecting in the library | Medium |
| CHD-1026 | Laptop overheating and shutting down | Low |
| CHD-1027 | Print credits not added | Low |
| CHD-1028 | Guest Wi-Fi not working for visitors | Medium |

## After Prompt 2 (Status = Open and Priority = High)
List rows returns **0** rows from tickets.csv: the file has 4 High tickets, but none of them is Open
(3 are Closed, CHD-1017 is In progress).

## Prove the filter works
Add one ticket: Title "Exam hall projector dead", Priority High, Status Open.
Test the flow manually: List rows now returns **1** row more than before (exactly 1 if the only
Open High tickets are the ones you add now) and the email lists that title.

Note: Open High tickets from earlier labs (for example Tablet screen cracked from Lesson 3.2 or the
test tickets from Lesson 4.3) also appear after Prompt 2. That is correct behaviour.
