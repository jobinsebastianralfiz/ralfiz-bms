// Ralfiz Money · starter. Work through TODO(1) to TODO(7).
const KEY = 'ralfiz-money';
const CATS = {
  food: { label: 'Food', icon: '🍛', color: '#f97316' },
  travel: { label: 'Travel', icon: '🚕', color: '#0ea5e9' },
  bills: { label: 'Bills', icon: '💡', color: '#8b5cf6' },
  shopping: { label: 'Shopping', icon: '🛍️', color: '#ec4899' },
  health: { label: 'Health', icon: '💊', color: '#10b981' },
};
// Amounts are whole paise; dates are 'YYYY-MM-DD' strings.
const SEED = [
  { id: 1, title: 'Office rent share', amount: 1200000, cat: 'bills', date: '2026-09-01' },
  { id: 2, title: 'Team lunch', amount: 185000, cat: 'food', date: '2026-09-12' },
  { id: 3, title: 'Cab to Kochi airport', amount: 142050, cat: 'travel', date: '2026-09-18' },
  { id: 4, title: 'Groceries', amount: 312075, cat: 'food', date: '2026-08-28' },
];
const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });
const money = (paise) => inr.format(paise / 100);
const monthFmt = new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric', timeZone: 'UTC' });
const dayFmt = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', timeZone: 'UTC' });
const $ = (sel) => document.querySelector(sel);
const el = (tag, className, text = '') => Object.assign(document.createElement(tag), { className, textContent: text });
const NS = 'http://www.w3.org/2000/svg';
const form = $('#form');
const state = { expenses: load(), month: 'all', editId: null };

function load() {
  // TODO(1): return the parsed array from localStorage.getItem(KEY),
  // or SEED when nothing is stored or the JSON is corrupted (try/catch).
  return [];
}
function commit(expenses) {
  // TODO(1): set state.expenses, save it with JSON.stringify, then render().
  state.expenses = expenses;
  render();
}

function visible() {
  // TODO(2): filter by state.month ('all' or 'YYYY-MM') and sort newest date first.
  return state.expenses;
}

function render() {
  renderMonths();
  const list = visible();
  // TODO(2): total = sum of amounts; sums = [{ cat, sum }] from Object.groupBy, biggest first.
  const total = 0;
  const sums = [];
  $('#total').textContent = money(total);
  $('#count').textContent = list.length;
  $('#top').textContent = sums[0] ? CATS[sums[0].cat].label : '—';
  renderList(list);
  renderChart(sums, total);
}

function renderMonths() {
  const months = [...new Set(state.expenses.map((e) => e.date.slice(0, 7)))].sort().reverse();
  if (!months.includes(state.month)) state.month = 'all';
  $('#month').replaceChildren(new Option('All months', 'all'),
    ...months.map((m) => new Option(monthFmt.format(new Date(m + '-01')), m)));
  $('#month').value = state.month;
}

function renderList(list) {
  // TODO(3): for each expense clone $('#row').content.firstElementChild,
  // set data-id, icon, title, "Food · 12 Sept", amount and aria-labels with textContent/setAttribute.
  $('#list').replaceChildren();
  $('#empty').hidden = list.length > 0;
}

function renderChart(sums, total) {
  // TODO(6): remove old .seg circles, then for each { cat, sum } append an SVG circle
  // (createElementNS) with stroke-dasharray "pct 100-pct" and stroke-dashoffset starting at 25.
  // Fill #legend with one <li> per category (use --c for the dot colour).
  $('#center').textContent = money(total);
}

function resetForm() {
  state.editId = null;
  form.reset();
  form.elements.date.value = new Date().toLocaleDateString('en-CA');
  $('#formTitle').textContent = $('#save').textContent = 'Add expense';
  $('#cancel').hidden = true;
}

form.addEventListener('submit', (ev) => {
  ev.preventDefault();
  // TODO(4): read FormData, build { title, amount (paise, Math.round), cat, date },
  // then commit a new array: add with a Date.now() id, or map to update state.editId.
  console.log('TODO(4): save', Object.fromEntries(new FormData(form)));
});

// TODO(5): one click listener on #list. Find button[data-act] with closest().
// 'del' → commit without it, then toast('Deleted …', undo) where undo() commits it back.
// 'edit' → set state.editId, copy values into form.elements, change the headings, show Cancel.

let toastTimer;
function toast(message, onUndo) {
  const box = $('#toast');
  box.replaceChildren(message);
  if (onUndo) {
    const undo = el('button', '', 'Undo');
    undo.addEventListener('click', onUndo);
    box.append(undo);
  }
  box.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => box.classList.remove('show'), 4000);
}

function csvCell(value) {
  // TODO(7): prefix "'" when the value starts with = + - @, and quote cells that
  // contain a comma, a double quote or a line break (double the inner quotes).
  return String(value);
}
function exportCsv() {
  // TODO(7): build rows (header + visible()), join with ',' and '\r\n', make a Blob,
  // create an object URL, click a temporary <a download>, then revoke the URL.
  console.log('TODO(7): export', visible().length, 'rows');
}

$('#month').addEventListener('change', (ev) => { state.month = ev.target.value; render(); });
$('#cancel').addEventListener('click', () => { resetForm(); render(); });
$('#export').addEventListener('click', exportCsv);
form.elements.cat.replaceChildren(...Object.entries(CATS).map(([k, c]) => new Option(`${c.icon} ${c.label}`, k)));
resetForm();
render();
