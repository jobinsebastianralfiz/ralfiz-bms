# dm16 lab: Ralfiz Store sales dashboard

Draw a monthly revenue bar chart on a canvas and a sales-by-category donut
chart in SVG, both from sales.json.

## Run it
The page loads sales.json with fetch, so it must be served over http.
Open dom/dm16/start with VS Code Live Server, or run

    npx serve dom/dm16/start

and open the printed address.

## Tasks
Work through TODO(1) to TODO(7) in app.js. The steps are in the lesson.

## Acceptance criteria
- The bar chart is sharp on a phone or with browser zoom at 200%
  (canvas.width equals the CSS width × devicePixelRatio).
- Twelve bars with month labels and four ₹ grid lines appear, and the bars
  grow in over about 0.7 seconds (instantly with reduced motion).
- Hovering a bar highlights it and shows a tooltip such as "Mar · ₹8,18,000".
- The donut shows five segments that add up to a full circle, starting at
  12 o'clock. Hovering or tabbing to a segment or legend row highlights both
  and shows that category in the centre.
- Resizing the window redraws the bar chart at the new width, still sharp.
- No errors in the console.
