# Lab 1.2 - Settings and pricing

Build the two most common "change the page" features of a real product: a
**theme switcher** (Light / Dark / System plus an accent colour) and a
**monthly/yearly pricing switch**.

You will use `dataset`, `classList.toggle`, `setAttribute` for ARIA state,
`style.setProperty` for CSS custom properties, `getComputedStyle` and
`textContent`. The CSS is finished: every colour is a custom property.

## Run it

Open `dom/dm3` in VS Code and start **Live Server** on `start/index.html`, or
run `npx serve` inside `dom/dm3` and open `/start/`. Keep DevTools open.

## Tasks (in `start/app.js`)

1. **TODO(1)** In `applyTheme`, set `document.documentElement.dataset.theme`
   and update the `active` class and `aria-checked` on the three buttons.
2. **TODO(2)** Save the choice in `localStorage` under `ralfiz-theme` and
   restore it on load with a `?? 'light'` fallback.
3. **TODO(3)** When the accent colour input changes, set `--accent` on the root
   with `style.setProperty` and log the Save button's computed background.
4. **TODO(4)** In `setBilling`, read `data-monthly` / `data-yearly` with
   `dataset`, format with `Intl.NumberFormat` and write with `textContent`.
5. **TODO(5)** Set `aria-pressed` on the billing buttons and
   `document.body.dataset.billing` so the CSS can show the Save 20% badge.

## Acceptance criteria

- Clicking **Dark** turns the page dark, the Dark button looks selected, and
  `<html data-theme="dark">` is visible in the Elements panel.
- Reloading the page keeps the chosen theme.
- Picking a new accent colour recolours the logo, buttons and the Pro plan
  border at once; the console logs an `rgb(...)` value.
- **Yearly** shows Pro at ₹399/mo "Billed ₹4,788 yearly", Team at ₹1,199/mo,
  and the Save 20% badge appears; **Monthly** shows ₹499 and ₹1,499.
- No errors in the console.

## Think about it

- Why is `aria-pressed="true"` a better source of truth for the billing
  buttons than a class like `.on`?
- The solution wraps `localStorage` in `try`/`catch`. When can storage throw?
- What would a user see if the theme were applied only after all images
  loaded? How do real sites avoid the "white flash" in dark mode?
