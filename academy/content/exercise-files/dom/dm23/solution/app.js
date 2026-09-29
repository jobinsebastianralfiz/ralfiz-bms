// Web Components solution: <rating-stars> (form-associated) and <product-card>.
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

const starsTemplate = document.createElement('template');
starsTemplate.innerHTML = `
  <style>
    :host { display: inline-flex; gap: 2px; font-size: 26px; line-height: 1; border-radius: 8px; cursor: pointer; }
    :host(:focus-visible) { outline: 3px solid #c7d2fe; outline-offset: 2px; }
    span { color: #d7dbe7; transition: transform .12s; }
    span.on { color: var(--star-color, #f59e0b); }
    span:hover { transform: scale(1.18); }
  </style>
  <div id="stars" part="stars"></div>`;

class RatingStars extends HTMLElement {
  static formAssociated = true;
  static observedAttributes = ['value', 'max'];
  #internals;

  constructor() {
    super();
    this.attachShadow({ mode: 'open' }).append(starsTemplate.content.cloneNode(true));
    this.#internals = this.attachInternals();
    this.addEventListener('click', (ev) => {
      const star = ev.composedPath().find((n) => n.dataset?.v);
      if (star) this.#commit(Number(star.dataset.v));
    });
    this.addEventListener('keydown', (ev) => {
      const keys = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1 };
      if (ev.key in keys) this.#commit(this.value + keys[ev.key]);
      else if (ev.key === 'Home') this.#commit(1);
      else if (ev.key === 'End') this.#commit(this.max);
      else return;
      ev.preventDefault();
    });
  }
  get value() { return Number(this.getAttribute('value')) || 0; }
  set value(v) { this.setAttribute('value', v); }
  get max() { return Number(this.getAttribute('max')) || 5; }

  connectedCallback() {
    if (!this.hasAttribute('tabindex')) this.tabIndex = 0;
    this.#internals.role = 'slider';
    this.render();
  }
  attributeChangedCallback() { this.render(); }

  render() {
    const stars = Array.from({ length: this.max }, (_, i) => {
      const s = document.createElement('span');
      s.textContent = '★';
      s.dataset.v = i + 1;
      s.classList.toggle('on', i < this.value);
      return s;
    });
    this.shadowRoot.getElementById('stars').replaceChildren(...stars);
    Object.assign(this.#internals, { ariaValueMin: '1', ariaValueMax: String(this.max),
      ariaValueNow: String(this.value), ariaValueText: `${this.value} of ${this.max} stars` });
    this.#internals.setFormValue(String(this.value));
  }
  #commit(v) {
    const next = Math.min(this.max, Math.max(1, v));
    if (next === this.value) return;
    this.value = next;
    this.dispatchEvent(new CustomEvent('rating-change', { detail: { value: next }, bubbles: true, composed: true }));
  }
}
if (!customElements.get('rating-stars')) customElements.define('rating-stars', RatingStars);

const cardTemplate = document.createElement('template');
cardTemplate.innerHTML = `
  <style>
    :host { display: flex; flex-direction: column; gap: 6px; background: #fff; border: 1px solid #e5e7ef; border-radius: 16px; padding: 10px; }
    .media { position: relative; aspect-ratio: 4 / 3; border-radius: 12px; display: grid; place-items: center; font-size: 46px; background: var(--tint, #eef2ff); }
    .badge { position: absolute; top: 8px; left: 8px; font-size: 11px; font-weight: 700; color: #fff; background: var(--accent, #4f46e5); border-radius: 6px; padding: 1px 7px; }
    .badge:empty { display: none; }
    h3 { margin: 4px 0 0; font-size: 15px; }
    p { margin: 0; color: #64748b; font-size: 13px; flex: 1; }
    .row { display: flex; flex-wrap: wrap; gap: 6px; justify-content: space-between; align-items: center; }
    .price { font-weight: 700; font-size: 16px; }
    button { font: inherit; font-weight: 600; border: 0; border-radius: 10px; padding: 7px 12px; color: #fff; white-space: nowrap; background: var(--accent, #4f46e5); cursor: pointer; }
  </style>
  <div class="media" part="media"><span id="emoji"></span><span class="badge" part="badge" id="badge"></span></div>
  <h3><slot name="title">Untitled product</slot></h3>
  <p><slot>No description yet.</slot></p>
  <div class="row"><span class="price" part="price" id="price"></span><button part="button" type="button">Add to cart</button></div>`;

class ProductCard extends HTMLElement {
  static observedAttributes = ['price', 'emoji', 'badge'];
  constructor() {
    super();
    this.attachShadow({ mode: 'open' }).append(cardTemplate.content.cloneNode(true));
    this.shadowRoot.querySelector('button').addEventListener('click', () => {
      this.dispatchEvent(new CustomEvent('add-to-cart', {
        bubbles: true, composed: true,
        detail: { title: this.productTitle, price: Number(this.getAttribute('price')) },
      }));
    });
  }
  get productTitle() { return this.querySelector('[slot=title]')?.textContent.trim() ?? 'Untitled product'; }
  connectedCallback() { this.render(); }
  attributeChangedCallback() { this.render(); }
  render() {
    const $ = (id) => this.shadowRoot.getElementById(id);
    $('emoji').textContent = this.getAttribute('emoji') ?? '🛍️';
    $('badge').textContent = this.getAttribute('badge') ?? '';
    $('price').textContent = usd.format(Number(this.getAttribute('price')) || 0);
    this.shadowRoot.querySelector('button').setAttribute('aria-label', `Add ${this.productTitle} to cart`);
  }
}
if (!customElements.get('product-card')) customElements.define('product-card', ProductCard);

// ---- page code: talks to components only through attributes, properties and events ----
let items = 0;
let cents = 0;
document.querySelector('#grid').addEventListener('add-to-cart', (ev) => {
  items += 1;
  cents += Math.round(ev.detail.price * 100);
  document.querySelector('#cart').textContent = `🛒 ${items} items · ${usd.format(cents / 100)}`;
});
const review = document.querySelector('#review');
review.addEventListener('rating-change', (ev) => console.log('rating-change', ev.target.getAttribute('name'), ev.detail.value));
review.addEventListener('submit', (ev) => {
  ev.preventDefault();
  const data = Object.fromEntries(new FormData(review));
  console.log('Review:', data);
  document.querySelector('#summary').textContent = `Thanks! Quality ${data.quality}/5, delivery ${data.delivery}/5.`;
});
