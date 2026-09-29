# dm23 · Web Components: <rating-stars> and <product-card>

Build two reusable custom elements with Shadow DOM and use them on a Ralfiz Store page.

## Run it
app.js is an ES module, so serve the folder:

    npx serve start        # or VS Code Live Server

## Tasks (TODOs in start/app.js and start/style.css)
1. TODO(1) RatingStars: attach an open shadow root, clone the template, create ElementInternals.
2. TODO(2) value/max getters and setters that reflect to attributes; observedAttributes.
3. TODO(3) render(): max stars, value of them "on"; internals.ariaValueNow/ariaValueText; form value.
4. TODO(4) click, arrow keys, Home, End; dispatch rating-change (bubbles, composed) only for user actions.
5. TODO(5) ProductCard: named slot "title", default slot, parts media/badge/price/button, add-to-cart event.
6. TODO(6) page: one add-to-cart listener on the grid; theme one card with --accent and ::part(button).

## Acceptance criteria
- Tabbing to a rating and pressing Right Arrow raises it by one star; the console logs one rating-change.
- Setting document.querySelector('rating-stars').value = 5 in the console updates the stars without an event.
- Submitting the review form logs quality=4 etc.: the ratings take part in FormData.
- The .promo card is pink purely through --accent; page rules like "button { … }" do not change the card buttons.
- Clicking Add to cart on any card updates the header count and total.
