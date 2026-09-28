# Business Card (lesson 2.2)

Your first real Flutter app: a one-screen business card with a seed-colour
theme and automatic dark mode. Add it to your portfolio.

## Setup

    flutter create business_card
    cd business_card

Replace lib/main.dart with start/lib/main.dart and delete
test/widget_test.dart (it tests the default counter app). You can also paste
the file into DartPad.

## Tasks

1. TODO(1) and TODO(2): hide the debug banner and add a teal seed theme.
2. TODO(3): add the AppBar with a centred title and a share action.
3. TODO(4) and TODO(5): avatar with initials, name and job title, all styled
   from Theme.of(context).
4. TODO(6): the contact Card. Remove the temporary ContactRow and Text lines
   the starter shows.
5. TODO(7): dark theme and ThemeMode.system.

## Acceptance criteria

- No DEBUG ribbon in the top-right corner.
- The AppBar title "My Card" is centred and a share icon sits on the right.
- The avatar, name, job title and card are centred on the screen as a group.
- There is no hard-coded colour in CardPage or ContactRow: every colour
  comes from colorScheme.
- When the phone or computer switches to dark mode, the app switches too
  with no code changes.
- flutter analyze reports no issues.
