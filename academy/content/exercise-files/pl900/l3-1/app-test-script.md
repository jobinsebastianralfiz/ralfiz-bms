# Canvas app test script (Lesson 3.1)

Start state: the Ticket table holds the 28 rows from **tickets.csv** (CHD-1001 to CHD-1028).
If you already added extra test tickets in earlier labs, your totals will be higher by that number.

| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Play the app with the search box empty | Gallery lists all 28 tickets |
| 2 | Type **Print** | 2 tickets: "Printer out of toner in library", "Print credits not added" |
| 3 | Type **Pr** | 3 tickets: the two above plus "Projector not working in Hall B" |
| 4 | Type **Laptop** | 2 tickets: "Laptop will not charge", "Laptop overheating and shutting down" |
| 5 | Type **print** (lower case) | Same 2 tickets as step 2 (StartsWith ignores case) |
| 6 | Clear the box, choose Open in ddStatus (optional part) | 6 tickets (CHD-1023 to CHD-1028) |
| 7 | Press + and add: Title "Test - ignore me", Priority Low | Gallery shows 29 tickets |
| 8 | Edit the test ticket, change Priority to Medium, save | Gallery shows Medium for it |
| 9 | Delete the test ticket | Gallery is back to 28 tickets |

## App checker
Open App checker > Accessibility before and after setting **AccessibleLabel** on the search box.
The warning about the missing accessible label on txtSearch should disappear.
