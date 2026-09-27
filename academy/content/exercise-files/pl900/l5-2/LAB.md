# PL-900 · 5.2 Topics: conversation paths

## Files
- log-ticket-topic.md

## Steps
1. Download log-ticket-topic.md.
2. In your agent, create a topic from blank named Log a ticket and add the description from the file (or the trigger phrases for classic orchestration).
3. Add Question node 1 and save the response in a variable named ProblemTitle.
4. Add Question node 2 with the options Low, Medium and High, saved as Priority.
5. Add the Message node that repeats both variables, inserting them with the variable picker. Save the topic.
6. Open the Greeting system topic and replace its message with the text in the file.
7. Run the 4 test conversations in the test pane.

## Check your work
- [ ] Test 1: the agent repeats Printer in lab 2 jams and High.
- [ ] Test 2: My laptop is not working starts Log a ticket without typing the topic name.
- [ ] Test 3: the greeting shows Monday to Friday 8:00 to 18:00 and Saturday 9:00 to 13:00.
- [ ] Test 4: typing super urgent at the priority question makes the agent ask again.
