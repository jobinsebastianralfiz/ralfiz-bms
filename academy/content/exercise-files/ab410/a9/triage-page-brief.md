# Triage board: generative page brief

Requested by: Divya Nair (Team lead, City campus)
App: Help Desk Staff (model-driven)
Tables to add as data: Ticket, Category

## Why
Every morning the team opens the Active Tickets view and scrolls to find what to pick up
first. Divya wants one page that shows the open queue by priority, like a whiteboard.

## Description to paste (first prompt)

    Build a triage board for help desk staff. Show tickets whose Status is Open as cards
    in three columns: High, Medium and Low priority, in that order from left to right.
    Each column header shows the priority name and the number of cards in it.
    Each card shows the Ticket Number, Title, Category name, Campus and Due Date.
    Sort cards in each column by Due Date, earliest first.
    Each card has a button "Start work" that sets the ticket Status to In progress and
    removes the card from the board.
    Use a clean, light layout with the priority name written as text on every card,
    not only shown by colour.

## Follow-up prompts (one at a time)
1. Add a Category filter at the top of the page with an "All categories" option.
2. Show the Due Date in red with the word "Overdue" when it is before today.
3. Add a small refresh button next to the filter that reloads the tickets.

## Acceptance tests (with tickets.csv imported)
| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Open the page | 6 cards: High 0, Medium 3, Low 3 |
| 2 | Read the Medium column | CHD-1023, CHD-1025, CHD-1028 |
| 3 | Read the Low column | CHD-1024, CHD-1026, CHD-1027 |
| 4 | Filter Category = Network | 2 cards: CHD-1025 and CHD-1028 |
| 5 | Select Start work on CHD-1027 | Card disappears; Low shows 2; the ticket shows In progress in the Active Tickets view |
| 6 | Look at due dates | Every card says Overdue, because all due dates are on or before 3 Sep 2026 |

After test 5, set CHD-1027 back to Open in the ticket form so the numbers in later labs still match.

## Things to check in the Code tab
- Find where the page reads the Ticket table and which columns it selects.
- Find the filter on Status and confirm it compares with the Open choice value, not the label text.
- Find the update call made by the Start work button.
