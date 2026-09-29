// Lab 1.1 - Inventory inspector (starter)
// Every TODO is about SELECTING or TRAVERSING. The rendering helpers are done.

// Writes label/value pairs into the details panel (uses textContent: safe).
function showDetails(title, facts) {
  const details = document.querySelector('#details');
  const h2 = document.createElement('h2');
  h2.textContent = title;
  const dl = document.createElement('dl');
  for (const [label, value] of facts) {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = label;
    dd.textContent = value;
    dl.append(dt, dd);
  }
  details.replaceChildren(h2, dl);
}

// TODO(1): select the list with getElementById('list') and all products
// inside it with querySelectorAll('.product'). Show the count in #total.
const list = null;
const products = [];

// TODO(2): select the out-of-stock products with an attribute selector
// ('.product[data-stock="0"]'), add the class 'out' to each one and
// show how many there are in #out.

// TODO(3): loop over products and find the one with the lowest
// Number(item.dataset.price). Show its <h2> text in #cheapest.

// TODO(4): when the list is clicked, find the clicked product with
// event.target.closest('.product'). If there is one, move the 'selected'
// class to it and call showDetails() with its name, category, price,
// stock, and the names of its previousElementSibling and nextElementSibling
// (or 'none').
if (list) {
  list.addEventListener('click', (event) => {
    console.log('clicked', event.target.tagName);
  });
}

// TODO(5): when a filter button is clicked, read its data-filter selector,
// give that button the 'active' class (and remove it from the others), and
// toggle 'dim' on every product that does NOT match the selector:
//   product.classList.toggle('dim', !product.matches(selector))

console.log('Starter loaded. Products selected so far:', products.length);
