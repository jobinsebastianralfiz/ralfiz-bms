# Help desk booking app with AI (Lesson 3.5)

## Prompt 1: Power Apps home page
An app for students to book a 15-minute slot with the help desk. Each booking has the
student's email, the date, the start time, the campus (North, South or City), the topic
(Network, Hardware, Accounts, Software, Printing or Classroom AV) and a short note.

## Expected table (compare with Copilot's proposal)
| Column | Type |
|--------|------|
| Booking title (primary) | Text |
| Student email | Email (or text) |
| Booking date | Date only |
| Start time | Text or date and time |
| Campus | Choice: North, South, City |
| Topic | Choice (6 options) |
| Note | Multiple lines of text |

Adjust at least one column so it matches this table (for example change Campus from text to a choice).

## Prompt 2: Copilot pane in Power Apps Studio
Add a screen called Tomorrow that lists only the bookings where the booking date is tomorrow,
sorted by start time, with a button to go back to the main screen.

What to look for: the gallery Items formula filters the booking date against Today() plus one day,
for example with DateAdd(Today(), 1).

## Prompt 3: generative page in your model-driven app (Help Desk Staff)
A page that summarises tickets with Status Open, grouped by Category, with a count for each category.

## Prompt 4: vibe experience
Use the text of Prompt 1 again. Compare: number of tables, screens, and anything extra it built.

## Maker review checklist (before sharing)
- [ ] Column types are correct (dates are dates, choices are choices)
- [ ] Required columns: Student email, Booking date, Start time
- [ ] Security: students get a role that lets them create and read only their own bookings
- [ ] Tested: added, edited and deleted a booking
