// Lab 1.2 - Settings and pricing (solution)
const root = document.documentElement;
const themeButtons = document.querySelectorAll('[data-choice]');
const accentInput = document.querySelector('#accent');
const saveButton = document.querySelector('#save');
const statusEl = document.querySelector('#status');
const billing = document.querySelector('#billing');
const prefersDark = matchMedia('(prefers-color-scheme: dark)');

const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
});

// Storage can throw (private mode, blocked cookies): never let that break the page.
function load(key, fallback) {
  try { return localStorage.getItem(key) ?? fallback; } catch { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(key, value); } catch { /* ignore */ }
}

// ---------- Theme ----------
function applyTheme(choice) {
  const resolved = choice === 'system' ? (prefersDark.matches ? 'dark' : 'light') : choice;
  root.dataset.theme = resolved;
  themeButtons.forEach((btn) => {
    const selected = btn.dataset.choice === choice;
    btn.classList.toggle('active', selected);
    btn.setAttribute('aria-checked', String(selected));
  });
  save('ralfiz-theme', choice);
  console.log('theme choice:', choice, '-> resolved:', resolved);
}

themeButtons.forEach((btn) => {
  btn.addEventListener('click', () => applyTheme(btn.dataset.choice));
});
// If the user picked System, follow the OS when it changes.
prefersDark.addEventListener('change', () => {
  if (load('ralfiz-theme', 'light') === 'system') applyTheme('system');
});
applyTheme(load('ralfiz-theme', 'light'));

// ---------- Accent colour ----------
function applyAccent(colour) {
  root.style.setProperty('--accent', colour);
  accentInput.value = colour;
}

accentInput.addEventListener('input', () => {
  applyAccent(accentInput.value);
  console.log('accent', accentInput.value, '-> button', getComputedStyle(saveButton).backgroundColor);
});

saveButton.addEventListener('click', () => {
  save('ralfiz-accent', accentInput.value);
  statusEl.textContent = 'Preferences saved ✓';
  setTimeout(() => { statusEl.textContent = ''; }, 2500);
});
applyAccent(load('ralfiz-accent', '#7c3aed'));

// ---------- Pricing ----------
function setBilling(period) {
  for (const plan of document.querySelectorAll('.plan')) {
    const price = Number(plan.dataset[period]);
    plan.querySelector('.amount').textContent = price === 0 ? 'Free' : inr.format(price);
    plan.querySelector('.per').textContent = price === 0 ? '' : '/mo';
    plan.querySelector('.note').textContent = price === 0 ? 'Forever'
      : period === 'yearly' ? `Billed ${inr.format(price * 12)} yearly` : 'Billed monthly';
  }
  for (const btn of billing.querySelectorAll('button')) {
    btn.setAttribute('aria-pressed', String(btn.dataset.period === period));
  }
  document.body.dataset.billing = period;
  console.log('billing:', period);
}

billing.addEventListener('click', (event) => {
  const btn = event.target.closest('button');
  if (btn) setBilling(btn.dataset.period);
});
setBilling('monthly');
