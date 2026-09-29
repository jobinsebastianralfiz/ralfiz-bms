// Ralfiz Money · solution. Rule: event → new state → commit() (save + render).
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
  try { return JSON.parse(localStorage.getItem(KEY)) ?? SEED; } catch { return SEED; }
}
function commit(expenses) {
  state.expenses = expenses;
  try {
    localStorage.setItem(KEY, JSON.stringify(expenses));
  } catch (err) {
    toast('Could not save: storage is full or blocked');
    console.error(err);
  }
  render();
}

function visible() {
  return state.expenses
    .filter((e) => state.month === 'all' || e.date.startsWith(state.month))
    .toSorted((a, b) => b.date.localeCompare(a.date) || b.id - a.id);
}

function render() {
  renderMonths();
  const list = visible();
  const total = list.reduce((sum, e) => sum + e.amount, 0);
  const sums = Object.entries(Object.groupBy(list, (e) => e.cat))
    .map(([cat, items]) => ({ cat, sum: items.reduce((s, e) => s + e.amount, 0) }))
    .toSorted((a, b) => b.sum - a.sum);
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
  $('#list').replaceChildren(...list.map((e) => {
    const row = $('#row').content.firstElementChild.cloneNode(true);
    const cat = CATS[e.cat];
    row.dataset.id = e.id;
    row.classList.toggle('editing', e.id === state.editId);
    row.querySelector('.ico').textContent = cat.icon;
    row.querySelector('.ico').style.background = cat.color + '22';
    row.querySelector('.t').textContent = e.title;
    row.querySelector('.m').textContent = `${cat.label} · ${dayFmt.format(new Date(e.date))}`;
    row.querySelector('.amt').textContent = money(e.amount);
    row.querySelector('[data-act=edit]').setAttribute('aria-label', `Edit ${e.title}`);
    row.querySelector('[data-act=del]').setAttribute('aria-label', `Delete ${e.title}`);
    return row;
  }));
  $('#empty').hidden = list.length > 0;
}

function renderChart(sums, total) {
  $('#donut').querySelectorAll('.seg').forEach((n) => n.remove());
  const gap = sums.length > 1 ? 0.8 : 0;
  let offset = 25;
  for (const { cat, sum } of sums) {
    const pct = (sum / total) * 100;
    const seg = document.createElementNS(NS, 'circle');
    const attrs = { class: 'seg', cx: 21, cy: 21, r: 15.915, stroke: CATS[cat].color,
      'stroke-dasharray': `${pct - gap} ${100 - pct + gap}`, 'stroke-dashoffset': offset };
    for (const [k, v] of Object.entries(attrs)) seg.setAttribute(k, v);
    $('#donut').append(seg);
    offset -= pct;
  }
  $('#center').textContent = money(total);
  $('#legend').replaceChildren(...sums.map(({ cat, sum }) => {
    const li = el('li', '');
    li.style.setProperty('--c', CATS[cat].color);
    li.append(el('span', 'dot'), CATS[cat].label, el('span', 'val', money(sum)),
      el('b', '', `${Math.round((sum / total) * 100)}%`));
    return li;
  }));
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
  const data = Object.fromEntries(new FormData(form));
  const entry = { title: data.title.trim(), amount: Math.round(Number(data.amount) * 100),
    cat: data.cat, date: data.date };
  if (!entry.title || !(entry.amount > 0)) return;
  const next = state.editId
    ? state.expenses.map((e) => (e.id === state.editId ? { ...e, ...entry } : e))
    : [...state.expenses, { id: Date.now(), ...entry }];
  toast(state.editId ? 'Expense updated' : `Added ${entry.title}`);
  resetForm();
  commit(next);
});

$('#list').addEventListener('click', (ev) => {
  const btn = ev.target.closest('button[data-act]');
  if (!btn) return;
  const id = Number(btn.closest('.row').dataset.id);
  const item = state.expenses.find((e) => e.id === id);
  if (btn.dataset.act === 'del') {
    if (state.editId === id) resetForm();
    commit(state.expenses.filter((e) => e.id !== id));
    toast(`Deleted ${item.title}`, () => {
      commit([...state.expenses, item]);
      toast('Expense restored');
    });
    return;
  }
  const f = form.elements;
  state.editId = id;
  f.title.value = item.title;
  f.amount.value = (item.amount / 100).toFixed(2);
  f.cat.value = item.cat;
  f.date.value = item.date;
  $('#formTitle').textContent = 'Edit expense';
  $('#save').textContent = 'Save changes';
  $('#cancel').hidden = false;
  f.title.focus();
  render();
});

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
  let s = String(value);
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}
function exportCsv() {
  const rows = [['Date', 'Title', 'Category', 'Amount (INR)'],
    ...visible().map((e) => [e.date, e.title, CATS[e.cat].label, (e.amount / 100).toFixed(2)])];
  const csv = rows.map((r) => r.map(csvCell).join(',')).join('\r\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
  const link = el('a', '');
  link.href = URL.createObjectURL(blob);
  link.download = `ralfiz-expenses-${state.month}.csv`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  toast(`Exported ${rows.length - 1} expenses`);
}

$('#month').addEventListener('change', (ev) => { state.month = ev.target.value; render(); });
$('#cancel').addEventListener('click', () => { resetForm(); render(); });
$('#export').addEventListener('click', exportCsv);
form.elements.cat.replaceChildren(...Object.entries(CATS).map(([k, c]) => new Option(`${c.icon} ${c.label}`, k)));
resetForm();
render();
