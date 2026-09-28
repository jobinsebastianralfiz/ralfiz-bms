# Lab 2.5: Habit Tracker

Make a list of daily habits respond to taps, long presses and deletes, with
the right kind of feedback for each action.

## Files
- start/lib/main.dart: compiles and shows four habits, with TODO(1) to TODO(5).
- solution/lib/main.dart: the finished screen.

## Setup
1. Run: flutter create habit_tracker
2. Replace lib/main.dart with start/lib/main.dart.
3. Run it on a device, an emulator or DartPad. No packages are needed.

## Tasks
1. TODO(1): tap a habit to mark it done or not done.
2. TODO(2): delete with a SnackBar that offers Undo.
3. TODO(3): long press opens a bottom sheet with three options.
4. TODO(4): the reset button asks for confirmation in a dialog.
5. TODO(5): a Mark all done button that disables itself when there is nothing left.

## Acceptance criteria
- Tapping "Drink water" shows a ripple and switches its icon to a filled check circle; tapping again switches it back.
- Deleting "Stretch" removes it and shows "Deleted Stretch" with an Undo action; Undo puts it back in the same position.
- Deleting two habits quickly shows only the latest SnackBar (the first one is hidden).
- Long pressing a habit opens a sheet with a drag handle and Rename, Set reminder and Delete; Delete removes that habit.
- In the reset dialog, Cancel or tapping outside changes nothing; Reset clears every check.
- When all habits are done, Mark all done is greyed out and ignores taps.
