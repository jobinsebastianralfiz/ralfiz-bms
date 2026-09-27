# Report an IT problem: form and flows (Lesson 4.2)

## Microsoft Form: "Report an IT problem"
| # | Question | Type | Required | Options |
|---|----------|------|----------|---------|
| 1 | Title | Text | Yes | Short answer |
| 2 | Priority | Choice | Yes | Low, Medium, High |
| 3 | Your student email | Text | Yes | |

## Flow A: CHD - Form to ticket (automated)
1. Trigger: Microsoft Forms, When a new response is submitted (Form: Report an IT problem).
2. Microsoft Forms, Get response details (Response Id from the trigger).
3. Dataverse, Add a new row, Table: Tickets.
   - Title: the Title answer.
   - Status: Open.
   - Priority: a choice column needs its number, not the text. Use an expression like
     if(equals(PRIORITY_ANSWER,'High'),HIGH_VALUE,if(equals(PRIORITY_ANSWER,'Medium'),MEDIUM_VALUE,LOW_VALUE))
     Replace PRIORITY_ANSWER with the Priority answer from dynamic content, and the three
     *_VALUE words with the numbers shown for each option of your Priority column
     (open the column in the Ticket table and look at each choice's value).
4. Microsoft Teams, Post message in a chat or channel (or Office 365 Outlook, Send an email (V2) to yourself):
   "New ticket: " followed by the Title answer.

## Flow B: CHD - High priority approval (automated)
1. Trigger: Dataverse, When a row is added, modified or deleted (Added, Ticket, Organization).
2. Condition: Priority is equal to HIGH_VALUE.
3. Yes branch: Approvals, Start and wait for an approval.
   - Approval type: Approve/Reject - First to respond
   - Title: "High priority ticket: " plus Title
   - Assigned to: your own account (in real life: suresh.kumar@staff.example.edu)
4. After the approval, Condition: Outcome is equal to Approve.
   - Yes: Dataverse, Update a row (Ticket, row ID from trigger), Status = In progress.
   - No: Dataverse, Update a row, Status = Closed.

## Test data
Submit the form once for each row of **test-responses.csv**, in order.
For each High response, approve the first and reject the second.
