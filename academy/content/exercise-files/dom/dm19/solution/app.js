const products = [
  { id: 1, name: 'Wireless Mouse', price: 799 },
  { id: 2, name: 'Desk Lamp', price: 1499 },
  { id: 3, name: 'Notebook Set', price: 349 },
  { id: 4, name: 'USB-C Hub', price: 2199 },
];
const cart = new Map();
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const live = document.querySelector('#live');
const announce = (msg) => { live.textContent = msg; };

// Disclosure: Categories
const toggle = document.querySelector('#cat-toggle');
const panel = document.querySelector('#cat-panel');
const nav = toggle.closest('.cat');
function setOpen(open) {
  toggle.setAttribute('aria-expanded', String(open));
  panel.hidden = !open;
}
toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
nav.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !panel.hidden) {
    setOpen(false);
    toggle.focus();
  }
});
nav.addEventListener('focusout', (event) => {
  if (!nav.contains(event.relatedTarget)) setOpen(false);
});
document.addEventListener('click', (event) => {
  if (!nav.contains(event.target)) setOpen(false);
});

// Products with named Add buttons
document.querySelector('#products').append(...products.map((p) => {
  const li = document.createElement('li');
  li.className = 'card';
  const h3 = document.createElement('h3');
  h3.textContent = p.name;
  const price = document.createElement('p');
  price.textContent = inr.format(p.price);
  const add = document.createElement('button');
  add.type = 'button';
  add.className = 'btn primary';
  add.dataset.id = p.id;
  const hidden = document.createElement('span');
  hidden.className = 'sr-only';
  hidden.textContent = ' ' + p.name + ' to cart';
  add.append('Add', hidden);
  li.append(h3, price, add);
  return li;
}));

function totals() {
  const count = [...cart.values()].reduce((a, b) => a + b, 0);
  const sum = [...cart].reduce((s, [id, q]) => s + products.find((x) => x.id === id).price * q, 0);
  return count + ' item' + (count === 1 ? '' : 's') + ', ' + inr.format(sum);
}

function renderCart() {
  const lines = [...cart].map(([id, qty]) => {
    const p = products.find((x) => x.id === id);
    const li = document.createElement('li');
    li.dataset.id = id;
    const text = document.createElement('span');
    text.textContent = p.name + ' × ' + qty;
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'btn remove';
    remove.setAttribute('aria-label', 'Remove ' + p.name);
    remove.textContent = '✕';
    li.append(text, remove);
    return li;
  });
  document.querySelector('#lines').replaceChildren(...lines);
  document.querySelector('#total').textContent = cart.size ? 'Total: ' + totals().split(', ')[1] : 'Your cart is empty.';
}

document.querySelector('#products').addEventListener('click', (event) => {
  const add = event.target.closest('button[data-id]');
  if (!add) return;
  const id = Number(add.dataset.id);
  cart.set(id, (cart.get(id) ?? 0) + 1);
  renderCart();
  announce(products.find((x) => x.id === id).name + ' added. ' + totals() + '.');
});

document.querySelector('#lines').addEventListener('click', (event) => {
  const remove = event.target.closest('.remove');
  if (!remove) return;
  const li = remove.closest('li');
  const index = [...li.parentElement.children].indexOf(li);
  const name = products.find((x) => x.id === Number(li.dataset.id)).name;
  cart.delete(Number(li.dataset.id));
  renderCart();
  const buttons = document.querySelectorAll('#lines .remove');
  (buttons[index] ?? buttons[index - 1] ?? document.querySelector('#cart-heading')).focus();
  announce(name + ' removed. ' + (cart.size ? totals() + '.' : 'Your cart is empty.'));
});

renderCart();
