// Web Components starter. The elements are defined so the page loads; finish the TODOs.
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

const starsTemplate = document.createElement('template');
starsTemplate.innerHTML = `
  <style>
    :host { display: inline-flex; gap: 2px; font-size: 26px; line-height: 1; border-radius: 8px; cursor: pointer; }
    :host(:focus-visible) { outline: 3px solid #c7d2fe; outline-offset: 2px; }
    span { color: #d7dbe7; }
    span.on { color: var(--star-color, #f59e0b); }
  </style>
  <div id="stars"></div>`;

class RatingStars extends HTMLElement {
  static formAssociated = true;          // lets the element submit a value with its form
  static observedAttributes = [];        // TODO(2): ['value', 'max']

  constructor() {
    super();
    // TODO(1): attach an open shadow root, append a clone of starsTemplate.content,
    // and store this.attachInternals() in a private #internals field (declare it above).
    // TODO(4): add click and keydown listeners on this (see the lesson).
  }
  // TODO(2): get value / set value (reflect to the attribute), get max (default 5)

  connectedCallback() {
    if (!this.hasAttribute('tabindex')) this.tabIndex = 0;
    this.render();
  }
  attributeChangedCallback() { this.render(); }
  render() {
    // TODO(3): draw max stars in #stars with class "on" for i <= value,
    // set role and aria values on the internals, and call internals.setFormValue(String(value)).
  }
}
customElements.define('rating-stars', RatingStars);

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
  <div class="media"><span id="emoji"></span><span class="badge" id="badge"></span></div>
  <h3>TODO(5): a named slot "title"</h3>
  <p>TODO(5): a default slot</p>
  <div class="row"><span class="price" id="price"></span><button type="button">Add to cart</button></div>`;

class ProductCard extends HTMLElement {
  static observedAttributes = ['price', 'emoji', 'badge'];
  constructor() {
    super();
    this.attachShadow({ mode: 'open' }).append(cardTemplate.content.cloneNode(true));
    // TODO(5): on button click dispatch 'add-to-cart' (bubbles, composed) with { title, price } in detail.
  }
  get productTitle() { return this.querySelector('[slot=title]')?.textContent.trim() ?? 'Untitled product'; }
  connectedCallback() { this.render(); }
  attributeChangedCallback() { this.render(); }
  render() {
    const $ = (id) => this.shadowRoot.getElementById(id);
    $('emoji').textContent = this.getAttribute('emoji') ?? '🛍️';
    $('badge').textContent = this.getAttribute('badge') ?? '';
    $('price').textContent = usd.format(Number(this.getAttribute('price')) || 0);
    // TODO(5): add part="media|badge|price|button" in the template and an aria-label on the button.
  }
}
customElements.define('product-card', ProductCard);

// TODO(6): one 'add-to-cart' listener on #grid that updates #cart ("🛒 2 items · $64.49").
// TODO(4): one 'rating-change' listener on #review that logs the new value.
document.querySelector('#review').addEventListener('submit', (ev) => {
  ev.preventDefault();
  console.log('Review:', Object.fromEntries(new FormData(ev.target)));
});
