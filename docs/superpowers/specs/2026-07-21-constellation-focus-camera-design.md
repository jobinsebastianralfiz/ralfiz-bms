# Constellation focus camera — declutter the portfolio overview

2026-07-21 · approved by user (option A, "click a client to fly in")

## Problem

The portfolio constellation (`/`) draws all 35 clients with permanent name
labels, share chips, satellite beads and overdue chips at once. At real data
volume the labels collide and the picture is unreadable (screenshot from prod,
2026-07-21).

## Decisions (user-confirmed)

1. **No free wheel-zoom/pan.** Two states only: *overview* and *focus*.
   Clicking a client (canvas sphere or sidebar list item) flies the camera to
   it; an on-canvas "Overview" button and `Esc` fly back.
2. **Overview is calm.** Spheres, beams and satellite beads stay; all name
   labels, share chips and overdue chips go. A single label follows hover.
   Clients with attention items keep a small permanent rose marker so risk is
   never hidden. The core "Ralfiz · N clients · M projects" label stays.

## Design

One camera `{x, y, scale}` in `pulse-graph.js`. World geometry (spheres,
beams, tethers, markers) draws under `ctx.translate/scale`; all text and chips
draw in screen space via `worldToScreen()` so type stays crisp and constant--
size at any zoom. Hit-testing maps the mouse through the inverse transform.

- **Overview**: camera identity. No per-node text except the hovered node's
  label+share chip and the core label. Flagged nodes (any satellite
  `needs_attention` or overdue `tag`) get a rose edge dot.
- **Focus**: camera eases (~600 ms, easeInOutCubic) to frame the selected
  client at ~2.2×, anchored left-of-center (clear of the right panel).
  Non-focused clients, their beams and satellites fade to ~15% alpha ghosts —
  still clickable to re-fly. The focused client's satellites lerp out into a
  wider fan and regain full labels: project name, status, overdue chip.
- **Selection vs camera**: the right detail panel keeps its current behaviour
  (boot selects the first client, list highlights). Flying is additive:
  boot does NOT fly; clicks do. Returning to overview keeps the selection.
- **Reduced motion**: camera and satellite fan jump instantly (t=1).
- **Overview button**: HTML overlay on the canvas stage, visible only in
  focus mode; `Esc` does the same.

## Scope

`static/js/pulse-graph.js` (camera, states, drawing split), `static/css/pulse.css`
(button + hover cursor), `templates/pulse/graph_dashboard.html` (button).
No backend, template-data or API changes. Deferred: free zoom/pan, clustering,
label culling by billing share.

## Verification

Screenshot overview and focus states via the browse tooling against dev
server data; check hover label, flagged markers, Esc/button return, reduced
motion path, and that the right panel still populates on click.
