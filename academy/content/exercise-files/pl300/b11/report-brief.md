# Report brief: Help Desk Overview page

**Requested by:** Suresh Kumar, help desk manager
**Audience:** campus leads (Anu, Rahul, Meera) and the IT director
**Used:** weekly team meeting on a projector, and on laptops

## Questions the page must answer
1. How many tickets did we log from January to June 2026?
2. Which category produces the most tickets?
3. Is the monthly volume going up or down?
4. Who is carrying the open work right now?

## Required visuals
| Visual | Fields | Answers |
|---|---|---|
| Card | [Ticket Count] | Q1 |
| Clustered bar chart | Categories[Name], [Ticket Count], sorted by count, largest first | Q2 |
| Line chart | 'Date'[Month] on the X-axis, [Ticket Count] | Q3 |
| Matrix | AssignedTo on rows, Status on columns, [Ticket Count] as values, background colour scale | Q4 |
| Slicers | Campus (tile or dropdown), Priority | Filtering |

## Rules
- A page-level filter excludes blank Campus values, in case the source sends unassigned rows later.
- Apply the team theme helpdesk-theme.json so every report uses the same colours. You may change one colour to make the matrix easier to read.
- Page size 16:9. Title text box at the top left: "Help Desk Overview, Jan to Jun 2026".
- Month must sort January to June, not alphabetically.
- No more than eight visuals on the page.

## Out of scope
- Printing. If finance later wants a printable monthly list of tickets, that is a paginated report built in Power BI Report Builder, not this page.

## Summary text
Add either a Copilot narrative (if your workspace has the right capacity) or a Narrative visual with two or three sentences a manager could read aloud.