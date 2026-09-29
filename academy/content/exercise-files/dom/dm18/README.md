# Lab 5.1 - Speed up the Order Dashboard

The dashboard in `start/` works, but it renders 5,000 order rows into the DOM, thrashes
layout when it sizes the revenue bars, redraws on every resize event and animates a toast
by changing `bottom`. Your job is to measure it, then fix it step by step.

## Run it

Open the folder with VS Code **Live Server**, or run `npx serve` in `dom/dm18/start`.

## Tasks

- TODO(1) `app.js`: add performance marks around the first render and log the measure.
- TODO(2) `updateBars()`: batch all reads, then all writes.
- TODO(3) Replace `renderAllRows()` with a virtual list (`#viewport`, `#spacer`, `#rows`).
- TODO(4) Throttle the scroll handler with requestAnimationFrame; make it passive.
- TODO(5) Debounce the resize handler (150 ms).
- TODO(6) Animate the toast with a CSS class (transform + opacity), not `bottom`.
- TODO(7) `style.css`: `content-visibility: auto` on `.report`, plus reduced-motion styles.

## How to measure

1. DevTools > Performance, gear icon, CPU: **4x slowdown**.
2. Record, reload the page, stop. Note the long task and the Layout blocks.
3. Repeat after each TODO.

## Acceptance criteria

- The console logs the render measure, e.g. `render: 8.8 ms` (it was far higher before).
- Only a few dozen `.row` elements exist at any time (check in the Elements panel).
- Resizing the window calls `updateBars` once after you stop dragging.
- The toast slides in smoothly and does not move at all with reduced motion enabled.
