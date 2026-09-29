// Lab 2.3 - Keyboard, pointer and custom events
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
}

// TODO(1): write openPalette() (show overlay, clear input, active = 0, render,
//          focus the input) and closePalette() (hide overlay, focus #trigger)

// TODO(2): a keydown listener on document:
//   - Ctrl+K or Cmd+K (event.key.toLowerCase() === 'k'): preventDefault and toggle
//   - '/' opens the palette, but only when the target is not an input/textarea

// TODO(3): keydown on the input: ArrowDown / ArrowUp move 'active' with wrap-around,
//          Enter runs matches[active], Escape closes. Ignore event.isComposing.
//          Call preventDefault only for the keys you handle. 'input' re-renders.

// TODO(4): runCommand(cmd): close the palette and dispatch a bubbling
//          CustomEvent('command', { detail: { id, label } }) from the palette.
//          Also: click on an option runs it; click on the backdrop closes.

// TODO(5): document listens for 'command':
//          'theme' toggles body.dark; 'go:*' sets #page to the name after "Go to ";
//          #status reads 'Last command: <label>'

// TODO(6): resizable sidebar with pointer events on #handle:
//          pointerdown -> setPointerCapture; pointermove (only while captured) ->
//          set --sidebar on document.documentElement between 160 and 360px;
//          lostpointercapture removes the 'dragging' class.
//          Bonus: ArrowLeft / ArrowRight on the focused handle change it by 16px.

document.querySelector('#trigger').addEventListener('click', () => {
  console.log('TODO(1): open the palette here');
});
