# Lab 2.3: Tip Calculator with bill splitting

Build a one-screen Tip Calculator that keeps its data in a State object.

## Files
- start/lib/main.dart: compiles and runs, with TODO(1) to TODO(4).
- solution/lib/main.dart: the finished app.

## Setup
1. Run: flutter create tip_calculator
2. Replace tip_calculator/lib/main.dart with start/lib/main.dart.
3. Run: flutter run (or paste the file into DartPad at dartpad.dev).

No packages are needed.

## Tasks
1. TODO(1): create a TextEditingController for the bill, attach it to the TextField and dispose it.
2. TODO(2): add a people count (starting at 1) with minus and plus buttons.
3. TODO(3): derive tip, total and per-person amounts inside build.
4. TODO(4): show Tip, Total and Each person pays in three cards.

## Rules
- Only the bill controller, the tip percentage and the people count are stored as fields.
- Tip, total and per-person amounts are computed in build, never stored.
- Money is shown with two decimals using toStringAsFixed(2).

## Acceptance criteria
- With an empty bill, all amounts show 0.00 and nothing crashes.
- Bill 1200 with 15% shows Tip 180.00 and Total 1380.00.
- Choosing 20% changes the Tip to 240.00 and the Total to 1440.00.
- With 4 people and a 1200 bill at 20%, Each person pays shows 360.00.
- The minus button is disabled when the count is 1.
- Typing letters such as "abc" shows 0.00 instead of an error.
