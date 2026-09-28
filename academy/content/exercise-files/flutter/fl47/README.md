# Lesson 8.4 lab: make the Photo Feed smooth

start/lib/main.dart is a working but slow feed of 1,000 photo posts. It has
six deliberate problems, each marked with a TODO. Measure, fix, measure again.

Photos come from https://picsum.photos (random placeholder images). Without
internet the cards show a broken-image icon, which is fine for this lab.

## Setup

    flutter create photo_feed
    cd photo_feed

Replace lib/main.dart with start/lib/main.dart. Connect a real phone if you can.
Run on Android, iOS or desktop: Isolate.run is not supported on the web
(Flutter's compute() is the web-friendly alternative).

## 1. Measure

1. flutter run --profile
2. Open DevTools (IDE command "Open DevTools" or the link in the terminal).
3. Performance view: scroll the feed quickly for a few seconds, tap the sort
   button a few times, then tap Stats. Note the slow frames.
4. Memory view: note the heap size after scrolling to the bottom.

## 2. Fix (TODOs in lib/main.dart)

- TODO(1) Sorting runs inside build(). Sort once in _toggleSort and keep
  the sorted list in state.
- TODO(2) ListView(children: ...) builds all 1,000 cards. Use ListView.builder.
- TODO(3) Cards have local "liked" state but no key. Add key: ValueKey(post.id).
- TODO(4) Images decode at full size. Pass cacheWidth (screen width x
  devicePixelRatio, rounded).
- TODO(5) _computeStats blocks the UI thread. Use Isolate.run.
- TODO(6) Add const to widgets that never change (the analyzer lists them).

## 3. Measure again

Repeat the same actions in profile mode and compare the frame chart and
memory with your notes.

## Acceptance criteria

- Liking post 0 and then deleting it leaves post 1 with an empty heart.
- While Stats runs, the spinner keeps turning, then the banner shows
  "216816 primes below 3,000,000".
- The sort button switches between newest-first and most-liked order.
- flutter analyze reports no prefer_const_constructors issues in lib/main.dart
  (enable it in analysis_options.yaml if your lints do not include it).
- In profile mode, scrolling shows fewer slow frames than before the fixes.
