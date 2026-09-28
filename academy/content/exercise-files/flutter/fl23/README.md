# Lab 3.2: Recipe Book, part 2 - decorated recipe cards

Turn a plain list of recipes into designed cards with Container and
BoxDecoration, and keep the list readable on wide screens with ConstrainedBox.

## Files
- start/lib/main.dart: compiles and shows plain ListTiles, with TODO(1) to TODO(5).
- solution/lib/main.dart: the finished list.

## Setup
1. Reuse your recipe_book project from lesson 3.1 or run: flutter create recipe_book
2. Replace lib/main.dart with start/lib/main.dart and run it.
3. Also run it in Chrome (flutter run -d chrome) or as a desktop app so you can
   resize the window. DartPad works too. No packages are needed.

## Tasks
1. TODO(1): RecipeCard as a decorated Container with margin and padding.
2. TODO(2): Thumbnail as a 72 x 72 gradient box with rounded corners.
3. TODO(3): title and category in an Expanded Column.
4. TODO(4): a pill-shaped time label.
5. TODO(5): Center + ConstrainedBox(maxWidth: 600) around the list.

## Rules
- Use withValues(alpha: ...) for transparent colours, not withOpacity.
- Do not pass color and decoration to the same Container.
- Take colours from Theme.of(context).colorScheme, except the recipe colours.

## Acceptance criteria
- Four cards show with rounded corners, a thin outline and a soft shadow,
  with a visible gap between cards.
- Each thumbnail uses its recipe colour: orange biryani, green stew, amber
  appam and purple payasam.
- The long biryani title wraps onto two lines and the "90 min" pill stays on
  the right.
- On a window wider than 600 pixels, the cards stop at 600 and stay centred;
  on a phone they fill the width minus the 16 px margins.
- The debug console shows no layout errors.

## Stretch goal
Add a LayoutBuilder around the ListView that prints its constraints, then
resize the window and explain the values you see.
