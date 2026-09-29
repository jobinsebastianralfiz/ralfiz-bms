// Lab 1.2 - Settings and pricing (starter)
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

// ---------- Theme ----------
function applyTheme(choice) {
  const resolved = choice === 'system' ? (prefersDark.matches ? 'dark' : 'light') : choice;
  // TODO(1): set root.dataset.theme to resolved, then loop over themeButtons:
  // toggle the 'active' class and set aria-checked to 'true' / 'false'
  // depending on whether btn.dataset.choice === choice.

  // TODO(2): save the choice with localStorage.setItem('ralfiz-theme', choice).
  console.log('theme choice:', choice, '-> resolved:', resolved);
}

themeButtons.forEach((btn) => {
  btn.addEventListener('click', () => applyTheme(btn.dataset.choice));
});

// TODO(2): restore the saved theme instead of always using 'light':
// localStorage.getItem('ralfiz-theme') ?? 'light'
applyTheme('light');

// ---------- Accent colour ----------
accentInput.addEventListener('input', () => {
  // TODO(3): root.style.setProperty('--accent', accentInput.value);
  // then log getComputedStyle(saveButton).backgroundColor
});

saveButton.addEventListener('click', () => {
  statusEl.textContent = 'Preferences saved ✓';
});

// ---------- Pricing ----------
function setBilling(period) {
  for (const plan of document.querySelectorAll('.plan')) {
    // TODO(4): read the price with Number(plan.dataset[period]).
    // Write 'Free' or inr.format(price) into .amount, '' or '/mo' into .per,
    // and into .note: 'Forever', 'Billed monthly' or
    // `Billed ${inr.format(price * 12)} yearly`. Use textContent.
  }
  // TODO(5): set aria-pressed on each billing button ('true' for the
  // chosen period) and set document.body.dataset.billing = period.
  console.log('billing:', period);
}

billing.addEventListener('click', (event) => {
  const btn = event.target.closest('button');
  if (btn) setBilling(btn.dataset.period);
});
setBilling('monthly');
