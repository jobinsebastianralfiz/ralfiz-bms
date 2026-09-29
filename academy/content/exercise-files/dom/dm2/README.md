# Lab 1.1 - Inventory inspector

The Ralfiz Store team wants a quick admin view of their inventory. The products
are already in `index.html`. Your job is to **select** and **traverse** them:
count, highlight, inspect and filter, without changing the HTML.

## Run it

Open `dom/dm2` in VS Code and start **Live Server** on `start/index.html`, or
run `npx serve` inside `dom/dm2` and open `/start/`. Keep DevTools open (F12).

## Tasks (in `start/app.js`)

1. **TODO(1)** Select the list with `getElementById` and the products with
   `querySelectorAll`. Show the count in `#total`.
2. **TODO(2)** Select sold-out products with `.product[data-stock="0"]`,
   add the class `out` to each and show the count in `#out`.
3. **TODO(3)** Find the cheapest product (read `dataset.price`, convert with
   `Number`). Show its name in `#cheapest`.
4. **TODO(4)** On a click anywhere in the list, use
   `event.target.closest('.product')` to find the card. Mark it `selected` and
   show its details, including the names of its previous and next siblings.
5. **TODO(5)** Filter buttons: read `data-filter`, and dim the products that do
   not `matches()` the selector.

## Acceptance criteria

- The summary shows **8** products, **2** out of stock, cheapest **Bamboo Pen Stand**.
- The two sold-out products show a red, crossed-out price and a Sold out label.
- Clicking the emoji, the name or the price of a product selects the same card
  and the panel lists Previous and Next (the first product shows Previous: none).
- Clicking **Desk** dims everything except the three desk products; **In stock**
  dims the two sold-out ones; **All** shows everything.
- No errors in the console.

## Think about it

- In the console, run `list.append(list.firstElementChild.cloneNode(true))`.
  Does `products.length` change? Does `list.children.length`? Why?
- Why does `closest('.product')` still work if you wrap the price in a `<span>`,
  when `event.target.parentElement` would not?
