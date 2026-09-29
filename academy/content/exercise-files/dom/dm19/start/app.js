const products = [
  { id: 1, name: 'Wireless Mouse', price: 799 },
  { id: 2, name: 'Desk Lamp', price: 1499 },
  { id: 3, name: 'Notebook Set', price: 349 },
  { id: 4, name: 'USB-C Hub', price: 2199 },
];
const cart = new Map();
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });

// TODO(3): turn this into a disclosure (button, aria-expanded, hidden, Escape, focusout)
document.querySelector('#cat-toggle').addEventListener('click', () => {
  document.querySelector('#cat-panel').classList.toggle('open');
});

// TODO(5): the Add "button" is a div and has no product in its name
document.querySelector('#products').append(...products.map((p) => {
  const li = document.createElement('li');
  li.className = 'card';
  const h3 = document.createElement('h3');
  h3.textContent = p.name;
  const price = document.createElement('p');
  price.textContent = inr.format(p.price);
  const add = document.createElement('div');
  add.className = 'btn primary';
  add.dataset.id = p.id;
  add.textContent = 'Add';
  li.append(h3, price, add);
  return li;
}));

function renderCart() {
  const lines = [...cart].map(([id, qty]) => {
    const p = products.find((x) => x.id === id);
    const li = document.createElement('li');
    li.dataset.id = id;
    const text = document.createElement('span');
    text.textContent = p.name + ' × ' + qty;
    const remove = document.createElement('div'); // TODO(1)/(5): a real, named button
    remove.className = 'btn remove';
    remove.textContent = '✕';
    li.append(text, remove);
    return li;
  });
  document.querySelector('#lines').replaceChildren(...lines);
  const total = [...cart].reduce((s, [id, q]) => s + products.find((x) => x.id === id).price * q, 0);
  document.querySelector('#total').textContent = cart.size ? 'Total: ' + inr.format(total) : 'Your cart is empty.';
}

document.querySelector('#products').addEventListener('click', (event) => {
  const add = event.target.closest('[data-id]');
  if (!add) return;
  const id = Number(add.dataset.id);
  cart.set(id, (cart.get(id) ?? 0) + 1);
  renderCart();
  // TODO(4): announce the change in a live region
});

document.querySelector('#lines').addEventListener('click', (event) => {
  const remove = event.target.closest('.remove');
  if (!remove) return;
  cart.delete(Number(remove.closest('li').dataset.id));
  renderCart();
  // TODO(6): move focus to the next Remove button or the cart heading
});

renderCart();
