# Build the daily summary flow with Copilot (Lesson 4.4)

## Prompt 1: Power Automate home page
Every day at 5 pm, list Dataverse tickets with status Open and email me a summary.

Expected draft (names can differ slightly):
| Step | What Copilot should propose |
|------|-----------------------------|
| Trigger | Recurrence: frequency Day, interval 1, at 17:00 |
| Action | Microsoft Dataverse, List rows (table Tickets) with a filter on Status |
| Action | Office 365 Outlook, Send an email (V2) |

Before you accept, check the connections panel: Dataverse and Office 365 Outlook should both
show a green tick. Sign in to any that do not.

## Check the filter
Open List rows and look at **Filter rows**. It should look like
statuscolumn eq NUMBER, where statuscolumn is the logical name of your Status column
and NUMBER is the value of the Open choice. If Copilot guessed a wrong name or number, fix it.

## Prompt 2: Copilot pane in the designer
Only include tickets with High priority.

Expected change: the filter becomes something like
statuscolumn eq OPEN_NUMBER and prioritycolumn eq HIGH_NUMBER

## Prompt 3: if a run fails
Explain why this step failed and how to fix it.

## Prompt 4: make the email readable (optional)
Put each ticket title and due date on its own line in the email body.

## Optional: Power Automate for desktop
Build a flow that renames every file in a folder by adding today's date in front of the name.
Test it on a copy folder with three empty text files.
