# Lesson 3.5 lab: adaptive Recipe Book

Make the Recipe Book adapt to the window width.

| Window size | Width | Layout |
|---|---|---|
| compact | under 600 | Bottom NavigationBar, list only, tap opens a detail page |
| medium | 600 to 839 | NavigationRail with labels, list only, tap opens a detail page |
| expanded | 840 and up | Extended NavigationRail, list (320 wide) and detail side by side |

## Files
- start/lib/main.dart: always shows a bottom NavigationBar. Complete TODO(1) to TODO(5).
- solution/lib/main.dart: the finished adaptive app.

Run on a desktop, web or tablet target so you can resize the window.

## Acceptance criteria
- Below 600 px wide you see a bottom NavigationBar.
- From 600 px you see a NavigationRail with labels under the icons.
- From 840 px the rail is extended and the recipes show in two panes; "Pick a recipe" shows until you tap one.
- Switching tabs, then resizing the window, keeps the same tab selected.
- In landscape on a phone with a notch, no text is hidden under the cut-out.
