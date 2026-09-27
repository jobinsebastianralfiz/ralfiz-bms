# Help Desk Overview: charts and dashboard spec

All components are **system** components created in the Campus Help Desk solution,
so they travel to CHD Test with the solution.

## View: Open and in progress tickets (public view on Ticket)
- Columns: Ticket Number, Title, Category, Priority, Status, Due Date
- Filter: Status does not equal Closed
- Sort: Due Date ascending

## Chart 1: Tickets by category and priority
- Table: Ticket. Type: stacked column.
- Axis (horizontal): Category. Legend (series): Priority. Value: Title, aggregate Count.

Expected when shown with the **Active Tickets** view (all 28 rows are active):

| Category | High | Medium | Low | Total |
|----------|------|--------|-----|-------|
| Accounts | 1 | 4 | 0 | 5 |
| Classroom AV | 1 | 2 | 1 | 4 |
| Hardware | 1 | 3 | 1 | 5 |
| Network | 1 | 2 | 2 | 5 |
| Printing | 0 | 2 | 2 | 4 |
| Software | 0 | 1 | 4 | 5 |
| **Total** | 4 | 14 | 10 | 28 |

## Chart 2: Open tickets by status
- Table: Ticket. Type: pie.
- Axis: Status. Value: Title, aggregate Count.

| Shown with view | Slices |
|-----------------|--------|
| Active Tickets | Closed 16, In progress 6, Open 6 |
| Open and in progress tickets | In progress 6, Open 6 |

The chart definition is the same in both rows. Only the view changes the numbers.

## Dashboard: Help Desk Overview
- Type: classic dashboard, 2-column layout
- Top left: Chart 1 (default view: Active Tickets)
- Top right: Chart 2 (default view: Open and in progress tickets)
- Bottom, full width: list component showing the Open and in progress tickets view (12 rows)

## App changes
- Help Desk Staff: add a Dashboard page for Help Desk Overview and a Generative page
  for the triage board (see triage-page-brief.md), then Save and Publish.
