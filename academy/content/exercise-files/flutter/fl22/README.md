# Lab 3.1: Recipe Book, part 1 - the detail screen

The Recipe Book is the mini app for the Layout module. In this part you lay
out one recipe using only Row, Column, Expanded, Spacer-style flex and a
ListView. Lessons 3.2 and 3.3 add decorated cards and a hero banner.

## Files
- start/lib/main.dart: compiles, with TODO(1) to TODO(5).
- solution/lib/main.dart: the finished detail screen.

## Setup
1. Run: flutter create recipe_book
2. Replace lib/main.dart with start/lib/main.dart and run it.
   DartPad works too. No packages are needed.

## Tasks
1. TODO(1): title Row with an icon and an Expanded title.
2. TODO(2): stats Row with three equal Expanded InfoTiles.
3. TODO(3): InfoTile as a small Column.
4. TODO(4): scrolling ingredient list that fills the remaining height.
5. TODO(5): two buttons that share the bottom row equally.

## Acceptance criteria
- The long title "Grandma's slow-cooked Malabar chicken biryani" wraps onto
  two lines with no yellow-and-black overflow stripe.
- Time 90 min, Serves 6 and 520 kcal each take exactly one third of the width.
- Every ingredient quantity (500 g, 1 kg ... a handful) lines up at the right edge.
- The ingredient list scrolls on a small phone while the buttons stay at the bottom.
- Share and Start cooking have the same width.
- Turning the device to landscape (or making the window narrow in Chrome or on
  desktop) shows no overflow errors in the debug console.

## Stretch goal
Change the stats Row to give Time twice as much space as the other two tiles
with flex: 2, and explain the result.
