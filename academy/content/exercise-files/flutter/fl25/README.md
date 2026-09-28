# Lesson 3.4 lab: Recipe Book home screen

Build the Recipe Book home screen with slivers.

## Target design (top to bottom)
1. SliverAppBar.large with the title "Recipe Book" that collapses into a pinned bar.
2. A section title "Quick (30 min or less)".
3. A horizontal ListView.separated of QuickCard widgets, 120 px tall,
   showing only recipes with isQuick == true (Lemon Rice, Egg Roast, Banana Fritters).
4. A section title "All recipes".
5. A SliverGrid.builder of RecipeTile widgets using
   SliverGridDelegateWithMaxCrossAxisExtent(maxCrossAxisExtent: 220,
   mainAxisSpacing: 12, crossAxisSpacing: 12, childAspectRatio: 3 / 4).

## Files
- start/lib/main.dart: runs as a plain ListView. Complete TODO(1) to TODO(4).
- solution/lib/main.dart: the finished screen.

## Acceptance criteria
- The app runs with no layout errors in the debug console.
- Scrolling up shrinks the large title into a small pinned app bar.
- The quick row shows exactly 3 cards and scrolls sideways on its own.
- The grid shows all 8 recipes; on a phone in portrait it has 2 columns.
- Recipe names that are too long for a tile end with an ellipsis instead of overflowing
  (narrow the window to see it).
