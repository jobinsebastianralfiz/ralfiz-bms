# Widget Tree Explorer (lesson 2.1)

A counter app that logs every build, so you can see the widget and element
trees at work.

## Setup

    flutter create tree_explorer
    cd tree_explorer

Replace lib/main.dart with start/lib/main.dart. Run it on an emulator, a
device or Chrome with flutter run (or press F5 in VS Code) and keep the Debug
Console open. Delete test/widget_test.dart: it tests the default counter app.

## Tasks

1. TODO(1) to TODO(5) in lib/main.dart.
2. Experiment A - rebuilds: tap + three times. Note which build lines appear
   on each tap.
3. Experiment B - const: with the first Label const, tap again. Its line no
   longer appears.
4. Experiment C - hot reload: change the AppBar title to 'Tap Counter' and
   save (or press r in the terminal). The title changes, the count stays and
   'initState CounterPage' is NOT printed again.
5. Experiment D - hot restart: press R in the terminal (or the restart button).
   The count goes back to 0 and 'initState CounterPage' is printed again.
6. Experiment E - DevTools: open Flutter DevTools, choose the Widget Inspector,
   select the Chip on screen and find it in the tree under Scaffold > Center >
   Column.

## Acceptance criteria

- Each tap prints 'build CounterPage (count n)' and 'build Label(Count is n)'.
- After TODO(2), 'build Label(I am const)' is not printed on taps.
- The Chip reads 'Navigator above me: true', because MaterialApp creates a
  Navigator above the home page.
- Hot reload keeps the count; hot restart resets it to 0.
