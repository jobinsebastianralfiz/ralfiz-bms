# Business rule spec: High priority needs a description (Lesson 2.4)

## Requirement

Help desk agents cannot triage an urgent ticket without details.
When a ticket's Priority is High, Description must be business required.
When Priority is anything else, Description is optional.

## Rule design

| Setting | Value |
|---|---|
| Table | Ticket |
| Rule name | High priority needs description |
| Scope | Entity (all forms and the server) |
| Condition | Priority Equals High |
| Action if true | Set Business Required: Description = Business Required |
| Action if false (Else) | Set Business Required: Description = Not Business Required |

Without the Else action, Description stays required after you change Priority back to Low.

Save, then Activate the rule. A rule that is only saved does nothing.

## Test cases

Run each test on the Ticket main form (open the table, select a row, and edit it in the form). Do not save test changes unless the test says so.

| # | Start from | Do this | Expected result |
|---|---|---|---|
| 1 | CHD-1017 "Laptop will not charge" (High) | Open the row | Description shows the red required marker |
| 2 | CHD-1017 | Change Priority to Low | The required marker disappears |
| 3 | CHD-1017 | Set Priority back to High, clear Description, select Save | Save is blocked and Description is flagged as required |
| 4 | CHD-1001 "Printer out of toner in library" (Medium) | Clear Description | No required marker; the form would save (do not save) |
| 5 | New ticket | Choose High, leave Description empty, try to save | Save is blocked |

Discard your changes after tests 2 to 5.

## Why a business rule?

The requirement only needs "make a column required when a condition is true".
A business rule does this with no code, so it beats a flow or a plug-in.
