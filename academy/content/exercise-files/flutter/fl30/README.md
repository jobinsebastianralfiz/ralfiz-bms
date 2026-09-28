# Lesson 5.1 lab: Shop Catalog

Build the navigation for a small shop app with the imperative Navigator API.

## Screens
1. CatalogPage (home): products, a cart IconButton with a Badge showing the item count.
2. ProductPage: quantity stepper; "Add to cart" pops with the quantity.
3. CartPage: cart lines, total, a Delivery note field, "Place order" pops with true.

## Rules
- Data goes forward through constructors; results come back through pop.
- Check mounted after every await before using context.
- Back from CartPage asks "Discard your note?" when the note is not empty (PopScope).

## Files
- start/lib/main.dart: screens exist but are not connected. Complete TODO(1) to TODO(5).
- solution/lib/main.dart: the finished app.

## Acceptance criteria
- Adding 2 Headphones shows the SnackBar "Added 2 × Headphones" and the badge shows 2.
- Pressing Back on ProductPage adds nothing.
- The cart shows the total, for example Total: ₹3998 for 2 Headphones.
- With a note typed, Back shows the dialog; Stay keeps you on the cart, Discard returns to the catalog.
- Place order returns to the catalog, empties the cart and shows "Order placed".
