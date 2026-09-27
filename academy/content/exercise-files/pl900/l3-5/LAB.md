# PL-900 · 3.5 Build apps with AI

## Files
- booking-app-brief.md
- bookings-sample.csv

## Steps
1. Download the exercise files and open booking-app-brief.md.
2. On the Power Apps home page, paste Prompt 1. Compare Copilot’s proposed table with the Expected table and adjust at least one column, then create the app.
3. Play the app and add the 5 bookings from bookings-sample.csv, replacing TOMORROW and DAY AFTER TOMORROW with real dates.
4. In Power Apps Studio, open the Copilot pane and paste Prompt 2. Check the new screen’s gallery Items formula.
5. Play the app and open the Tomorrow screen.
6. Open your Help Desk Staff model-driven app in the designer, add a new page that you describe to Copilot, and use Prompt 3.
7. Try the vibe experience with Prompt 1 and compare the result, then complete the Maker review checklist.

## Check your work
- [ ] The booking table has the 7 columns in the Expected table (names may differ slightly).
- [ ] The Tomorrow screen shows exactly 2 bookings: Wi-Fi setup on new laptop (09:00) and MFA on new phone (09:15).
- [ ] The Tomorrow gallery’s Items formula uses Today() with one day added, for example DateAdd(Today(), 1).
- [ ] The generative page lists Open tickets by category; with only tickets.csv data it shows 6 Open tickets across 5 categories (Network has 2).
