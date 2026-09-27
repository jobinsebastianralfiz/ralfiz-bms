# SetPriorityFromKeywords: test cases (lesson D.9)

## What the plug-in must do
When a Ticket (chd_ticket) is created or its Title or Description changes, and the
text contains one of these keywords (any case), Priority becomes **High** before the
row is saved:

| Keyword | Example text that matches |
|---|---|
| outage | "Wi-Fi **outage** in library" |
| exam | "I have an **exam** on Monday" |
| fire | "Smoke from the projector, possible **fire** risk" |
| cannot log in | "I **cannot log in** to the LMS" |

Text without a keyword keeps the Priority the user chose.

## Choice values used in the code
This lab assumes the values that Dataverse gives a new local choice with the chd
publisher (option value prefix 10000):

| Column | Values |
|---|---|
| Priority (chd_priority) | Low = 100000000, Medium = 100000001, High = 100000002 |
| Status (chd_status) | Open = 100000000, In progress = 100000001, Closed = 100000002 |

Open the column in make.powerapps.com and check the values. If yours differ, change
PriorityHigh in SetPriorityFromKeywords.cs before you build.

## Step registrations
| Step | Message | Table | Stage | Mode | Filtering attributes | Image |
|---|---|---|---|---|---|---|
| 1 | Create | chd_ticket | PreOperation | Synchronous | (none) | (none) |
| 2 | Update | chd_ticket | PreOperation | Synchronous | chd_title, chd_description | Pre-image PreImage with chd_title, chd_description |

## Test cases
Run them in the Help Desk Staff app (or any model-driven form for Ticket). Set
the plug-in trace log setting to **All** first (in the environment's settings; in classic
System Settings it is "Enable logging to plug-in trace log" on the Customization tab).

| # | Action | Expected Priority | Expected trace text |
|---|---|---|---|
| T1 | Create a ticket, Title "Wi-Fi outage in library", Priority Low | High | "Keyword 'outage' found" |
| T2 | Create a ticket, Title "Printer out of toner in lab 3", Priority Low | Low | "No urgent keyword found" |
| T3 | Create a ticket, Title "Cannot Log In to the LMS", Priority Medium | High | "Keyword 'cannot log in' found" |
| T4 | Open CHD-1017 (description mentions an exam). Change Priority to Medium and save. | Medium (the plug-in does not run: Priority is not a filtering attribute) | no new trace row |
| T5 | On CHD-1017 change only the Title to "Laptop will not charge at all" and save | High (keyword exam comes from the pre-image description) | "Keyword 'exam' found" |
| T6 | Open CHD-1023 and change only Status to In progress | unchanged (Medium) | no new trace row |

## Why T5 matters
On Update, Target only contains the columns that changed. In T5 the Target holds the new
Title, but the Description (with "exam") is only in the pre-image. If you forget the
pre-image, T5 leaves Priority at Medium.

## Data check (tickets.csv)
Of the 28 tickets in tickets.csv, only **CHD-1017** contains a keyword (exam in its
description). CHD-1006 says "I cannot open email", which does not match "cannot log in".

## Clean up
Delete the tickets you created in T1 to T3, set CHD-1017 back to its original title
"Laptop will not charge" and set CHD-1023 back to Status Open, so later labs start from
the 28 rows of tickets.csv.