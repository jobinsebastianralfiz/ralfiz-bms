// Lab 2.3 - Keyboard, pointer and custom events (solution)
const COMMANDS = [
  { id: 'go:dashboard', label: 'Go to Dashboard', icon: '🏠' },
  { id: 'go:orders', label: 'Go to Orders', icon: '📦' },
  { id: 'go:products', label: 'Go to Products', icon: '🏷️' },
  { id: 'go:customers', label: 'Go to Customers', icon: '👥' },
  { id: 'theme', label: 'Toggle dark mode', icon: '🌙' },
];

const overlay = document.querySelector('#overlay');
const palette = document.querySelector('#palette');
const input = document.querySelector('#q');
const list = document.querySelector('#cmds');
const handle = document.querySelector('#handle');
const trigger = document.querySelector('#trigger');
let matches = COMMANDS;
let active = 0;

function render() {
  const q = input.value.trim().toLowerCase();
  matches = COMMANDS.filter((c) => c.label.toLowerCase().includes(q));
  active = Math.min(active, Math.max(matches.length - 1, 0));
  list.replaceChildren(...matches.map((cmd, i) => {
    const li = document.createElement('li');
    li.className = 'opt';
    li.id = `opt-${i}`;
    li.dataset.index = i;
    li.setAttribute('role', 'option');
    li.setAttribute('aria-selected', String(i === active));
    li.textContent = `${cmd.icon}  ${cmd.label}`;
    return li;
  }));
  if (!matches.length) {
    const li = document.createElement('li');
    li.className = 'none';
    li.textContent = 'No commands found';
    list.append(li);
  }
  input.setAttribute('aria-activedescendant', matches.length ? `opt-${active}` : '');
  list.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: 'nearest' });
}

// TODO(1): open and close
const isOpen = () => !overlay.hidden;
function openPalette() {
  overlay.hidden = false;
  input.value = '';
  active = 0;
  render();
  input.focus();
}
function closePalette() {
  overlay.hidden = true;
  trigger.focus(); // return focus to where the user came from
}

// TODO(2): global shortcuts
document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    isOpen() ? closePalette() : openPalette();
    return;
  }
  const typing = event.target.closest('input, textarea, [contenteditable]');
  if (event.key === '/' && !typing && !isOpen()) {
    event.preventDefault();
    openPalette();
  }
});

// TODO(3): keys inside the palette
input.addEventListener('keydown', (event) => {
  if (event.isComposing) return;
  const n = matches.length;
  if (event.key === 'ArrowDown' && n) active = (active + 1) % n;
  else if (event.key === 'ArrowUp' && n) active = (active - 1 + n) % n;
  else if (event.key === 'Enter') { event.preventDefault(); runCommand(matches[active]); return; }
  else if (event.key === 'Escape') { event.preventDefault(); closePalette(); return; }
  else return;
  event.preventDefault();
  render();
});
input.addEventListener('input', () => { active = 0; render(); });

// TODO(4): announce the command instead of acting on the page
function runCommand(cmd) {
  if (!cmd) return;
  closePalette();
  palette.dispatchEvent(new CustomEvent('command', {
    detail: { id: cmd.id, label: cmd.label },
    bubbles: true,
  }));
}
list.addEventListener('click', (event) => {
  const opt = event.target.closest('.opt');
  if (opt) runCommand(matches[Number(opt.dataset.index)]);
});
overlay.addEventListener('click', (event) => {
  if (event.target === overlay) closePalette();
});
trigger.addEventListener('click', openPalette);

// TODO(5): the app decides what commands mean
document.addEventListener('command', (event) => {
  const { id, label } = event.detail;
  if (id === 'theme') document.body.classList.toggle('dark');
  else if (id.startsWith('go:')) {
    document.querySelector('#page').textContent = label.replace('Go to ', '');
  }
  document.querySelector('#status').textContent = `Last command: ${label}`;
  console.log('command event', event.detail);
});

// TODO(6): resizable sidebar
const root = document.documentElement;
const setSidebar = (px) => {
  const width = Math.min(360, Math.max(160, px));
  root.style.setProperty('--sidebar', `${width}px`);
  return width;
};
let width = 220;

handle.addEventListener('pointerdown', (event) => {
  if (event.button !== 0) return;
  handle.setPointerCapture(event.pointerId);
  handle.classList.add('dragging');
});
handle.addEventListener('pointermove', (event) => {
  if (!handle.hasPointerCapture(event.pointerId)) return;
  width = setSidebar(event.clientX);
});
handle.addEventListener('lostpointercapture', () => {
  handle.classList.remove('dragging');
});
handle.addEventListener('keydown', (event) => {
  const delta = { ArrowLeft: -16, ArrowRight: 16 }[event.key];
  if (!delta) return;
  event.preventDefault();
  width = setSidebar(width + delta);
});
