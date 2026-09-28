# Lab 6.1: Water Tracker (setState, lifting state, InheritedWidget)

The starter has a classic bug: the glass count lives inside AddButtons, so the
header always says "0 of 8 glasses". Fix it step by step.

## Setup
1. flutter create water_tracker
2. Replace lib/main.dart with start/lib/main.dart. No packages are needed.

## Tasks
- TODO(1) Lift the count: add int _glasses and _add()/_remove() to _WaterHomeState.
- TODO(2) Make AddButtons stateless with onAdd and onRemove callbacks.
- TODO(3) Pass _glasses to ProgressHeader (remove the const from the children list).
- TODO(4) Implement WaterScope.of and updateShouldNotify.
- TODO(5) Wrap the Scaffold in WaterScope.
- TODO(6) Add const TodayCard() to the column. It takes no parameters, yet GlassGrid
  inside it must show the right number of filled drops.

## Acceptance criteria
- Tapping Add glass three times shows "3 of 8 glasses", a progress bar at 3/8 and
  three filled drops in the Today card.
- Remove never goes below 0.
- Log a glass (inside the Today card) also updates the header.
- At 8 glasses the header says "Goal reached. Well done!".
- Expanding the Hydration tip does not change the count, and adding a glass does not
  collapse the tip.

## Think about it
Put a debugPrint('TodayCard build') in TodayCard.build and one in GlassGrid.build.
Add a glass. Which one prints, and why?
