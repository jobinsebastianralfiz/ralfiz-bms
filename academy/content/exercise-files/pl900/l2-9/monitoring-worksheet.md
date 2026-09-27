# Monitoring worksheet (Lesson 2.9)

## Part A: capacity (admin center)

Open the admin center and find the capacity page (under Licensing or Resources, depending on your tenant).

| Storage type | Used | Notes |
|---|---|---|
| Database | | Tables and rows, e.g. your 28 tickets |
| File | | Attachments and images |
| Log | | Audit logs |

A developer environment may not count against tenant capacity, so the numbers can be small or not shown per environment. Write what you see.

## Part B: Monitor (Power Apps)

If you do not have a canvas app yet, create one from data using the Ticket table (Lesson 3.1 shows how). Then open it in edit mode and choose Advanced tools > Monitor, and play the app.

| Action in the app | Event(s) you saw in Monitor (category, operation) |
|---|---|
| App opens and the gallery loads | |
| Select a ticket | |
| Edit a ticket and save | |

Open one data event and write the data source name and the result: ______________________

## Part C: flow run history

Open any cloud flow. If you have none yet, create an instant flow with "Manually trigger a flow" and a Compose action whose input is Campus Help Desk test, then run it twice.

| Run start time | Status | Duration |
|---|---|---|
| | | |
| | | |

Open one run. For each step, note the green tick or red cross and one input or output value:

| Step | Result | One value |
|---|---|---|
| | | |
| | | |

Run history covers the last 28 days.

## Part D: which tool?

| Problem | Tool |
|---|---|
| The app is slow when the gallery loads | |
| A flow failed last night | |
| The environment is close to its storage limit | |
| Someone changed a ticket's priority and nobody knows who | |
