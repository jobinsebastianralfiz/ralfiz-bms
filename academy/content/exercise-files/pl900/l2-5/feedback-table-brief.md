# Ticket Feedback table brief (Lesson 2.5)

## The need

After a ticket is closed, the student rates the help desk from 1 to 5 and can add a comment.
Managers want to see low ratings per ticket.

## Prompt for Copilot

In Power Apps > Tables, start creating a table with Copilot and paste:

    A table to record student feedback on help desk tickets with a rating from 1 to 5, comments and a link to the ticket.

Then ask:

    Add a column for the date of the feedback.

## Target design (fix anything Copilot got different)

| Display name | Data type | Notes |
|---|---|---|
| Name (or Title) | Single line of text | Primary name column. Copilot may name it differently; keep it. |
| Rating | Whole number | Minimum 1, maximum 5 |
| Comments | Multiple lines of text | |
| Feedback date | Date only | |
| Ticket | Lookup to Ticket | The table you built in Lesson 2.2 |

Table name: Ticket Feedback.

Common Copilot guesses to fix:
- Rating created as a choice or decimal number: change it to Whole number.
- Ticket created as text: delete it and add a lookup to Ticket instead.
- Extra sample rows about unrelated tickets: delete them.

## Two rows to add (from feedback.csv)

| Name | Rating | Comments | Feedback date | Ticket (pick by title) |
|---|---|---|---|---|
| CHD-1001 feedback | 5 | Fixed quickly, thank you! | 2026-08-07 | Printer out of toner in library |
| CHD-1002 feedback | 2 | Took too long, I missed my class. | 2026-08-07 | Account locked after failed sign-ins |

The lookup shows the Ticket's primary name column (Title), not the ticket number.

## Second method: create a table from a file

Create another table from feedback.csv (New table > import or upload an Excel or CSV file). Name it Feedback Import.
Compare it with Ticket Feedback. Note which method gave you a real lookup to Ticket.
