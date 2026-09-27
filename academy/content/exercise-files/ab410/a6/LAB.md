# AB-410 · A.6 Prompt columns and row summaries

## Files
- prompts.txt
- test-tickets.csv

## Steps
1. Download the exercise files. In the Power Platform admin center, check that Copilot and AI prompts features and the AI insight cards setting are on for CHD Dev.
2. In the Campus Help Desk solution, add a column AI summary to Ticket with data type Prompt and clear Allow form fill assistance.
3. Select Add new prompt and paste the prompt column text from prompts.txt. Use +Add content to insert Title and Description where the brackets are.
4. Apply the filter Description contains data, test the prompt, then save the prompt and the column.
5. Create the four tickets from test-tickets.csv in Help Desk Staff. After a moment, refresh and read AI summary and its status column.
6. Under Customizations on Ticket, open Row summary and paste the row summary prompt from prompts.txt, inserting the five columns and LanguageCode. Select Test prompt.
7. Apply the row summary to main forms, open one of the new tickets, expand the summary bar, select Refresh and give thumbs-up feedback.
8. Open the Active Tickets view and use the inline Summary action on CHD-1017.

## Check your work
- [ ] The three tickets with a description get an AI summary whose "Suggested category" matches the last column of test-tickets.csv (Software, Classroom AV, Accounts).
- [ ] Printer offline in admin block keeps AI summary empty because its Description is blank.
- [ ] The 28 imported tickets have no AI summary until you edit their Title or Description.
- [ ] The row summary bar on a ticket shows five bullets (Title, Priority, Status, Due, Category) plus one urgency sentence.
- [ ] Ticket has no new column for the row summary: it is generated when viewed, not stored.
