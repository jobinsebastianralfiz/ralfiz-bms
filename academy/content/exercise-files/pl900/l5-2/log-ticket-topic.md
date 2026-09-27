# Topic spec: Log a ticket (Lesson 5.2)

## Topic details
- Name: Log a ticket
- Description (used by generative orchestration): Use when the user wants to report an IT problem.
- If your agent uses classic orchestration, add trigger phrases instead:
  report a problem, log a ticket, something is broken, my laptop is not working, I need IT help

## Nodes (top to bottom)
| # | Node | Settings |
|---|------|----------|
| 1 | Question | Text: What's the problem? Identify: User's entire response. Save as: ProblemTitle |
| 2 | Question | Text: How urgent is it? Identify: Multiple choice options: Low, Medium, High. Save as: Priority |
| 3 | Message | Thanks. I have noted: "{ProblemTitle}" with priority {Priority}. |
| 4 | End conversation (optional) | End with survey or End current topic |

In the Message node, insert the variables with the variable picker ({x}), do not type the braces.

## Greeting system topic
Replace the greeting message with:

    Hi, I'm Campus IT Helper. The help desk is open Monday to Friday 8:00 to 18:00
    and Saturday 9:00 to 13:00. How can I help?

## Test conversations (test pane, refresh between tests)
| # | You type | Then | Expected |
|---|----------|------|----------|
| 1 | I want to report a problem | Answer: Printer in lab 2 jams; choose High | Agent repeats "Printer in lab 2 jams" and High |
| 2 | My laptop is not working | Answer: Laptop will not charge; choose Medium | Log a ticket starts; repeats both values |
| 3 | Hi | | Greeting shows the help desk hours |
| 4 | I want to report a problem | Type "super urgent" at the priority question | Agent asks again (not one of the options) |
