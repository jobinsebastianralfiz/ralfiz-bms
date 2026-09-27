# Ticket Analyst: instructions, description and test questions (lesson D.14)

## Agent instructions (paste into the Foundry prompt agent)

    You are Ticket Analyst for the Campus Help Desk.
    You answer trend and statistics questions about many tickets, such as counts by
    category, priority or status, and lists of tickets that match a condition.
    Use only the Dataverse tools you have been given. The ticket table is chd_ticket and
    the category table is chd_category. Never create, update or delete data.
    Always say how many tickets you counted and list their ticket numbers when there are
    ten or fewer. If a question is about one student's own ticket, say that Help Desk
    Assistant handles single-ticket questions.
    If a tool call fails or returns nothing, say so plainly. Do not guess numbers.

## Description for the Copilot Studio Agents page

    Answers trend and statistics questions about many Campus Help Desk tickets, such as
    counts by category, priority or status, and lists of tickets that match a condition.
    Does not handle a single student's ticket status or create tickets.

## Test questions and expected answers
Expected answers come from the 28 rows of tickets.csv. If you added or changed tickets in
earlier labs, clean them up first, or your numbers will differ.

| # | Ask Ticket Analyst | Expected answer |
|---|---|---|
| Q1 | How many tickets have status Open? | 6: CHD-1023 to CHD-1028 |
| Q2 | Which category has the most Open tickets? | Network, with 2 (CHD-1025 and CHD-1028) |
| Q3 | How many tickets are not Closed? | 12 (6 Open and 6 In progress) |
| Q4 | How many tickets have High priority? | 4: CHD-1002, CHD-1009, CHD-1014, CHD-1017 |
| Q5 | Which tickets mention Wi-Fi in the title or description? | CHD-1025 and CHD-1028 |
| Q6 | Please close ticket CHD-1023. | The agent refuses or has no write tool to call. No data changes. |

## What to record for each test
- Which tool the agent asked to call, and the input it sent.
- Whether you approved it (require_approval is always).
- Whether the answer matches the table. If it does not, look at the tool input first:
  most wrong answers come from a wrong filter, such as comparing a choice column with its
  label instead of its stored number.

## Routing test in Copilot Studio (after Part D)
| Ask Help Desk Assistant | Expected route |
|---|---|
| What is the status of my ticket CHD-1023? | Help Desk Assistant answers itself |
| Which category has the most Open tickets? | Routed to Ticket Analyst; answer Network (2) |