// Lab 1.1 - Inventory inspector (solution)

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

const nameOf = (item) => item?.querySelector('h2').textContent ?? 'none';

// 1. Select once, reuse everywhere.
const list = document.getElementById('list');
const products = list.querySelectorAll('.product');      // static NodeList
document.querySelector('#total').textContent = products.length;

// 2. Attribute selector for out-of-stock items.
const soldOut = list.querySelectorAll('.product[data-stock="0"]');
soldOut.forEach((item) => item.classList.add('out'));
document.querySelector('#out').textContent = soldOut.length;

// 3. Loop over the NodeList to find the cheapest product.
let cheapest = products[0];
for (const item of products) {
  if (Number(item.dataset.price) < Number(cheapest.dataset.price)) cheapest = item;
}
document.querySelector('#cheapest').textContent = nameOf(cheapest);

// 4. One listener on the list; closest() finds the product card.
list.addEventListener('click', (event) => {
  const item = event.target.closest('.product');
  if (!item) return;
  list.querySelector('.selected')?.classList.remove('selected');
  item.classList.add('selected');
  const stock = Number(item.dataset.stock);
  showDetails(nameOf(item), [
    ['Category', item.dataset.category],
    ['Price', item.querySelector('.price').textContent],
    ['Stock', stock === 0 ? 'Sold out' : `${stock} units`],
    ['Previous', nameOf(item.previousElementSibling)],
    ['Next', nameOf(item.nextElementSibling)],
    ['Position', `${[...list.children].indexOf(item) + 1} of ${list.children.length}`],
  ]);
});

// 5. Filters: matches() tests each product against the button's selector.
const filters = document.querySelector('#filters');
filters.addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  const selector = button.dataset.filter;
  filters.querySelector('.active')?.classList.remove('active');
  button.classList.add('active');
  let shown = 0;
  products.forEach((product) => {
    const match = product.matches(selector);
    product.classList.toggle('dim', !match);
    if (match) shown += 1;
  });
  console.log(`${selector} -> ${shown} of ${products.length} products`);
});

filters.querySelector('button').classList.add('active');
console.log(`Loaded ${products.length} products, ${soldOut.length} sold out, cheapest: ${nameOf(cheapest)}`);
