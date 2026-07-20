# Design Prompt — Ralfiz PULSE Command Center (visual spec)

> This is a **design/frontend** prompt. It defines the exact look, feel, and motion
> of the command-center screen. Use it alongside the backend prompt (which defines
> `/api/pulse/ask/`). Give this to Claude Code for Phase 3 (the UI), or use it to
> build a standalone HTML mockup first. It's written to match a specific reference
> (the "Control AI · Policy Platform" knowledge-graph dashboard), re-skinned for
> Ralfiz BMS. Match these details precisely — they're what make it look premium
> instead of templated.

---

## 1. THE CONCEPT

A **knowledge-graph command center**, not a chart dashboard. The screen is a dark
canvas with a single luminous focal object and elegant connective lines. Two views,
toggled top-center:

- **Detail view (default):** one central entity (a glossy 3D orb) with curved
  tendrils flowing to a vertical stack of glass "count" cards on the right.
- **Graph view:** a full constellation — a bright ornate sun-core at center with
  light-beams radiating to dozens of glossy sphere-nodes, each a category, labelled
  with a name and a percentage.

For Ralfiz BMS the central entity is a **project** (e.g. "iRAD 2027"); the cards are
its related counts (Tasks, Milestones, Team, Blockers); the graph view is the whole
**portfolio** orbiting a Ralfiz core, each node a project or client colored by status.

---

## 2. PALETTE (use these exact values)

- Background base `#05090b`, with a radial teal vignette: center `#0a2429` →
  `#071316` → edge `#05090b`. Near-black, faint teal breath — NOT navy, NOT pure black.
- Primary accent (structure, glow, active): teal `#2fd4d4`, dim `#1a8a8a`.
- Selection / important accent: gold `#e8c07a`, bright `#f5d896`. Gold means "selected"
  or "priority" — use it on exactly ONE thing at a time.
- Node jewel tones (graph view): rose `#e08aa0`, violet `#a78bd6`, cyan `#7cc4e8`,
  used to encode category/status.
- Text: primary `#e9f2f4`, secondary `#7c94a0`, tertiary/labels `#4a5c66`.
- Glass fills: `rgba(20,40,46,.4)`; glass borders `rgba(120,220,220,.22)`.

Restraint rule: the palette is mostly darkness. Color appears only where it means
something. If more than ~15% of the screen is lit, it's too much — pull back.

---

## 3. TYPOGRAPHY

- One family is fine: **Inter** (already in the project via CDN). Personality comes
  from weight + spacing, not from a loud display face.
- Entity title: 28–32px, weight 700, tight tracking (-.3px). The year/number in the
  title gets the gold color as an accent.
- Kicker above the title: 11px, uppercase, letter-spacing 1.5px, teal.
- Card numbers: 30px/700; card labels: 13px/500 secondary.
- Tiny data tags on nodes: 10–11px, in small dark pill chips.

---

## 4. THE SIGNATURE ELEMENT — the 3D orb (get this exactly right)

This single object carries the whole "premium" impression. It is NOT a flat circle.

- A **sphere with real shading**: radial gradient offset toward the upper-left —
  bright core `#e6d4ff` → `#b89af0` → `#8a5fd6` → dark edge `#4a2a86`. A soft white
  **specular highlight** blob in the upper-left quadrant. A subtle **rim shadow** at
  the lower edge so it reads as lit from above-left.
- Around it, a **jagged reactive ring** — like an audio waveform bent into a circle —
  drawn as a spiky closed path that gently animates (layered sine noise), in a
  translucent teal + violet. Two passes, slightly different radius/opacity, for depth.
- A soft outer bloom (radial gradient, violet, fading to nothing).
- The orb sits left-of-center (~30% from left, ~55% down), not dead center — the
  cards balance it on the right.

Below the orb: a small **"GAPS 12"** pill (dark glass, gold number) and a **rating
chip** — a thumbs icon + a tiny horizontal meter with a red/amber fill.

---

## 5. TENDRILS (the connective lines)

- Thin **cubic-bezier curves** flowing from the orb's right side to each card's left
  edge — smooth S-curves, never straight spokes. Control points pull horizontally so
  lines leave the orb horizontally and arrive at the card horizontally.
- Default line: teal at ~28% opacity, 1px. The line to the SELECTED (gold) card is
  gold at ~55%, 1.6px.
- A **travelling light dot** runs along each curve (a small radial-gradient blob,
  teal or gold), looping — this is what makes it feel alive. Keep it slow.
- Include one extra "loose" tendril curving off-screen into nothing, like the
  reference — it implies more graph beyond the frame.

---

## 6. GLASS CARDS (right side, vertical stack)

- Frosted glass: `background: linear-gradient(135deg, rgba(30,70,78,.55),
  rgba(12,28,33,.35))`, `backdrop-filter: blur(12px)`, 1px border
  `rgba(120,220,220,.22)`, radius 16px.
- Inner top highlight: `inset 0 1px 0 rgba(255,255,255,.08)`; drop shadow
  `0 10px 30px rgba(0,0,0,.35)`.
- A **4px accent bar** down the left edge (teal, fading down). A soft radial glow
  bleeding from the top-right corner inside the card.
- Each card: a line-icon + big number on top, a secondary label under it.
- **Selected card = gold variant**: swap teal for gold in the bar, glow, border, plus
  a faint gold ring (`0 0 0 1px rgba(232,192,122,.4)`). Only one card gold at a time.
- Hover: lift/translate ~6px toward the orb, border brightens, shadow deepens.

---

## 7. TOP TOOLBAR (match the reference layout)

Left: logo (a small faceted sparkle mark) + "Ralfiz / Project Intelligence".
Center: pill-grouped icon buttons in frosted containers —
[graph-view | detail-view] toggle · [ + | − ] · [ filter•5 | sort•2 | AI-spark ].
Filter/sort carry tiny gold count badges.
Right: "＋ New Simulation" pill, a theme/moon icon, a search icon, an avatar chip
with a dropdown caret. Everything is frosted glass with the teal hairline border.

---

## 8. GRAPH VIEW (second screen)

- A central **sun-core**: an ornate concentric gold/bronze disc that glows and slowly
  rotates, labelled (e.g. "Ralfiz" or a hub project) with a percentage chip.
- **Light-beams** radiate outward — soft golden volumetric streaks, of varying length
  and brightness, toward the category nodes.
- **Category nodes**: glossy shaded spheres (same 3D treatment as the orb, smaller),
  jewel-toned by category, each with a text label + percentage. Smaller **satellite
  beads** hang off each node on thin dashed lines, carrying tiny number tags in pill
  chips.
- Gentle ambient motion: nodes bob slightly, beams shimmer, the whole field slowly
  parallaxes. On click of a node → animate/zoom into its Detail view.

---

## 9. MOTION (deliberate, not scattered)

- **Load:** the sun-core ignites first, then beams draw outward, then nodes fade/pop
  in along them (staggered). ~1.2s, ease-out.
- **Graph → Detail:** clicking a node zooms the camera toward it; other nodes fade;
  the chosen node becomes the central orb; cards slide in from the right with the
  tendrils drawing themselves.
- **Ambient (always on):** orb ring shimmer, travelling dots on tendrils, faint node
  bob. All slow and low-amplitude.
- **Answer arrives (command result):** the relevant card(s) pulse brighter, their
  tendril flares gold briefly, and a response panel eases up from the bottom.
- Respect `prefers-reduced-motion`: freeze ambient motion, keep only essential
  state changes.

---

## 10. COMMAND BAR (bottom — where voice/text lives)

- A wide frosted input pill centered at the bottom: a `>_` glyph, placeholder like
  "Ask PULSE — which projects are blocked · recap the agency", a **mic button**, and
  an **Execute** button (gold).
- Left of it, small chips: an agent selector, a "+N" attachments chip.
- On submit: show a thinking state (subtle), then the response panel + card reactions
  from §9. Mic uses the browser Web Speech API (input only) with a typed fallback.

---

## 11. QUALITY FLOOR (don't skip)

- Responsive: on narrow screens, cards stack below the orb; toolbar collapses into a
  menu; graph view becomes pan/zoomable.
- Visible keyboard focus rings (teal). Full keyboard path to send a command.
- Real empty/error/loading copy in the interface voice — never a raw traceback, never
  "undefined". An empty state invites the first command.
- All new CSS/JS self-contained (a `pulse.css` / `pulse.js`); do NOT modify the
  project's global `styles.css` or `app.js`.

---

## 12. WHAT TO AVOID (the cheap-imitation tells)

- Flat circles instead of shaded spheres. The orb MUST have specular + rim shading.
- Straight radial spokes instead of bezier curves.
- Neon overload / glow on everything — this design is mostly dark with restrained light.
- Generic SaaS card grid. The cards float and connect; they are not a dashboard grid.
- Pure black `#000` background (use the teal-tinted near-black).
- Bootstrap/Tailwind default components — everything here is bespoke.
