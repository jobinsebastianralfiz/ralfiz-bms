# Lesson 4.3 lab: refactor Travel Explorer into reusable widgets

The starter works, but HomePage is one long build method with helper methods.
Refactor it into small widgets without changing how the screen looks.

## Widgets to create
| Widget | Parameters |
|---|---|
| SectionHeader | required title, String? actionLabel, VoidCallback? onAction |
| DestinationCard | required destination, VoidCallback? onTap, Widget? trailing |
| StarRating | required int value, int max = 5, ValueChanged<int>? onChanged |

Then add ValueKey(item) to each PackingTile.

## Files
- start/lib/main.dart: working but messy. Complete TODO(1) to TODO(4).
- solution/lib/main.dart: the refactored version.

## Acceptance criteria
- The home screen looks the same as before the refactor, apart from the read-only rating
  on the Goa deal card.
- No method in HomePage starts with _build.
- Tapping the fourth star shows "4 of 5"; the read-only rating on the Goa card cannot be tapped.
- Tick Passport, remove it: Tickets and Charger stay unticked.
- Every custom widget has a const constructor with super.key.
