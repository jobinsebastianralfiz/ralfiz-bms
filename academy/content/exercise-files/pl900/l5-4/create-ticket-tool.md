# Tool spec: Create ticket (Lesson 5.4)

## Agent flow
Name: **Create ticket**

| Step | Action | Settings |
|------|--------|----------|
| 1 | When an agent calls the flow (trigger) | Inputs: Title (text), Priority (text) |
| 2 | Microsoft Dataverse, Add a new row | Table: Tickets. Title = Title input. Status = Open. Priority = expression below |
| 3 | Respond to the agent | Output: TicketId (text) = the new row's unique identifier from step 2 |

Priority expression (replace the three *_VALUE words with your Priority column's option numbers,
and PRIORITY_INPUT with the Priority input from dynamic content):

    if(equals(toLower(PRIORITY_INPUT),'high'),HIGH_VALUE,if(equals(toLower(PRIORITY_INPUT),'medium'),MEDIUM_VALUE,LOW_VALUE))

Input descriptions (the agent reads these to fill the inputs):
- Title: A short title for the IT problem, in the student's words.
- Priority: Low, Medium or High. High when the student says it is urgent or blocks an exam or class.

## Tool description
Creates a help desk ticket when a student reports a problem.

## Tests
Before testing, note how many rows the Ticket table has: ______

| # | You type | Expected |
|---|----------|----------|
| 1 | My laptop won't charge and it's urgent. | Agent may confirm the title, then calls Create ticket with Priority High and replies with an ID |
| 2 | The projector in room 110 is flickering | Agent asks how urgent it is (Priority is missing), then creates the ticket |
| 3 | How do I connect to Wi-Fi? | Agent answers from knowledge; the tool is NOT called |

After the tests, the Ticket table has 2 more rows than before. Open the activity map (or the test pane details)
to see which tool each message used.
