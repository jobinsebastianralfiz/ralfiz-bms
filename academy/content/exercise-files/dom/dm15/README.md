# dm15 lab: Ralfiz Academy live quiz leaderboard

A 90-second quiz round. Players score every 2 seconds, numbers count up,
rows glide to their new rank, and everything stops cleanly when time runs out.

## Run it
Open dom/dm15/start with VS Code Live Server, or run

    npx serve dom/dm15/start

and open the printed address.

## Tasks
Work through TODO(1) to TODO(6) in app.js. The steps are in the lesson.

## Acceptance criteria
- The clock counts down from 1:30 and stays correct if you switch tabs for
  20 seconds and come back (compare with your phone’s stopwatch).
- When a score changes, the number counts up smoothly instead of jumping.
- When the ranking changes, rows glide to their new place (no jumps).
- In DevTools > Rendering, "Emulate CSS prefers-reduced-motion: reduce" makes
  numbers and rows update instantly.
- At 0:00 the clock shows Finished, scores stop changing, and the winner row
  pulses once. The Performance panel shows no timers still running.
- While the tab is hidden, no rounds are played (scores are the same when
  you come back).
