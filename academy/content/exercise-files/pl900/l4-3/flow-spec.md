# High priority email flow (Lesson 4.3)

Name: **CHD - High priority alert**

| Step | Connector (standard or premium) | Trigger or action | Settings |
|------|--------------------------------|-------------------|----------|
| 1 | Microsoft Dataverse (premium) | Trigger: When a row is added, modified or deleted | Change type: Added. Table name: Tickets. Scope: Organization |
| 2 | Control (built in) | Condition | Priority (dynamic content) is equal to HIGH_VALUE |
| 3 | Office 365 Outlook (standard) | Send an email (V2), Yes branch | To: your address. Subject and body below |

## Priority value
Dataverse triggers return a choice column as a number. Open the Ticket table, open the Priority
column and note the number shown for **High**. Use that number as HIGH_VALUE in the condition.
Write it here: HIGH_VALUE = __________

## Email
Subject (expression): paste into the expression editor, then replace TITLE by selecting Title from dynamic content inside concat.

    concat('High priority ticket: ', TITLE)

Body (mix typed text and dynamic content):

    A new High priority ticket was logged.
    Title: [Title]
    Description: [Description]
    Due date: [Due date]
    Logged at (UTC): formatDateTime(utcNow(), 'yyyy-MM-dd HH:mm')

The last line is an expression; insert it with the expression editor.

## Test
Add the three rows in **test-tickets.csv** to the Ticket table one at a time
(Edit data, the canvas app, or the model-driven app). Wait for each run before adding the next.

## Run history questions
1. How many runs are listed? ____
2. In which runs did the condition go to the Yes branch? ____
3. Open one run: how long did the Send an email (V2) action take? ____
