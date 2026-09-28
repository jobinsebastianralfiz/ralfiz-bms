# Lab 3.3: Recipe Book, part 3 - hero banner and badge

Add a layered banner to the recipe detail page with Stack, Positioned and a
gradient scrim, and show a count on the shopping-list icon with Badge.

## Files
- start/lib/main.dart: compiles and shows a flat coloured box, with TODO(1) to TODO(5).
- solution/lib/main.dart: the finished page.

## Setup
1. Open your recipe_book project (or run: flutter create recipe_book).
2. Replace lib/main.dart with start/lib/main.dart and run it.
   DartPad works too. The photo comes from picsum.photos, so you need an
   internet connection to see it. No packages are needed.

## Tasks
1. TODO(1): Stack with StackFit.expand and the network photo.
2. TODO(2): transparent-to-black gradient scrim.
3. TODO(3): title and time pinned to the bottom with Positioned.
4. TODO(4): NEW pill top left and a favourite toggle top right.
5. TODO(5): Badge on the shopping-list icon.

## Layer order (back to front)
photo -> gradient -> title/time -> NEW pill -> favourite button

## Acceptance criteria
- The banner is 240 pixels tall and the photo fills it edge to edge without
  stretching.
- "Chicken biryani" and "90 min" are white, 16 pixels from the left and
  bottom edges, and readable even on a bright photo.
- With no internet, the banner shows the orange recipe colour instead of an
  error, and the text is still visible.
- Tapping the heart switches between an outline and a filled heart.
- The shopping-list icon shows no badge at first; after tapping
  "Add to shopping list" three times the badge shows 3.
- The debug console shows no "Incorrect use of ParentDataWidget" errors.

## Stretch goal
Replace the Positioned widgets of the NEW pill and heart with
Positioned.directional, using start/end instead of left/right and passing
textDirection: Directionality.of(context). Then add this to MaterialApp:
builder: (context, child) => Directionality(textDirection: TextDirection.rtl, child: child!),
and check that the pill and heart swap sides.
