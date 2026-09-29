# dm14 lab: Ralfiz Store infinite feed

Build a product feed that loads more products as you scroll, lazy-loads images,
fades cards in and switches to compact cards in narrow spaces.

Data: https://dummyjson.com/products?limit=12&skip=0 (total is 194 products).

## Run it
Open the dom/dm14/start folder with VS Code Live Server, or run

    npx serve dom/dm14/start

and open the printed address. fetch() needs http://, not file://.

## Tasks
Work through TODO(1) to TODO(6) in app.js. The steps are in the lesson.

## Acceptance criteria
- The first 12 products appear with a skeleton while they load.
- Scrolling near the end loads the next 12 before you reach the bottom,
  and the counter reads "24 of 194", then "36 of 194" and so on.
- Fast scrolling never shows the same product twice.
- At the end the message "You have seen all 194 products" appears and no
  more requests are sent (check the Network panel).
- Images have alt text, width and height, and loading="lazy"
  (Elements panel). No layout jump when they load.
- Cards fade in once; with "prefers-reduced-motion: reduce" emulated in
  DevTools (Rendering tab), they appear without movement.
- Making the window narrower than about 560px switches the grid to compact
  cards, and #width shows the grid width.
