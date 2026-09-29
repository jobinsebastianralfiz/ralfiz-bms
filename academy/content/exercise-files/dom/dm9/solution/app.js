// Ralfiz Academy course page: dialog, tabs, accordion and toasts.

// ---------- toast ----------
const toastRegion = document.querySelector('#toasts');

function toast(message, { duration = 4000 } = {}) {
  const el = document.createElement('div');
  el.className = 'toast';
  const text = document.createElement('p');
  text.textContent = message;
  const close = document.createElement('button');
  close.type = 'button';
  close.setAttribute('aria-label', 'Dismiss notification');
  close.textContent = '✕';
  el.append(text, close);
  toastRegion.append(el);

  let timer;
  let started;
  let remaining = duration;
  const start = () => {
    started = Date.now();
    timer = setTimeout(dismiss, remaining);
  };
  const pause = () => {
    clearTimeout(timer);
    remaining -= Date.now() - started;
  };
  function dismiss() {
    clearTimeout(timer);
    el.remove();
  }
  el.addEventListener('mouseenter', pause);
  el.addEventListener('mouseleave', start);
  close.addEventListener('click', dismiss);
  start();
  return { dismiss };
}

// ---------- tabs ----------
function initTabs(tablist) {
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];

  function select(tab, focus = false) {
    for (const t of tabs) {
      const selected = t === tab;
      t.setAttribute('aria-selected', String(selected));
      t.tabIndex = selected ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !selected;
    }
    if (focus) tab.focus();
  }

  tablist.addEventListener('click', (event) => {
    const tab = event.target.closest('[role="tab"]');
    if (tab) select(tab);
  });

  tablist.addEventListener('keydown', (event) => {
    const i = tabs.indexOf(document.activeElement);
    const last = tabs.length - 1;
    const moves = {
      ArrowRight: i === last ? 0 : i + 1,
      ArrowLeft: i === 0 ? last : i - 1,
      Home: 0,
      End: last,
    };
    if (!(event.key in moves)) return;
    event.preventDefault();
    select(tabs[moves[event.key]], true);
  });
}

// ---------- accordion ----------
function initAccordion(root) {
  root.addEventListener('click', (event) => {
    const btn = event.target.closest('.acc-btn');
    if (!btn) return;
    const open = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', String(!open));
    document.getElementById(btn.getAttribute('aria-controls')).hidden = open;
  });
}

// ---------- enroll dialog ----------
function initEnrollDialog() {
  const dialog = document.querySelector('#enroll');
  const openBtn = document.querySelector('#enroll-btn');
  const form = dialog.querySelector('form');

  openBtn.addEventListener('click', () => {
    form.reset();
    dialog.returnValue = '';
    dialog.showModal();
  });

  // Cancel is type="button", so Enter in a field submits "Reserve" instead
  dialog.querySelector('[data-close]').addEventListener('click', () => {
    dialog.close('cancel');
  });

  // Backdrop click closes (the form fills the dialog, so only the backdrop hits it)
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close('cancel');
  });

  dialog.addEventListener('close', () => {
    openBtn.focus();
    if (dialog.returnValue !== 'enroll') return;
    const data = Object.fromEntries(new FormData(form));
    toast(`Seat reserved for ${data.name} (${data.batch}). Check ${data.email}.`);
  });
}

initTabs(document.querySelector('[role="tablist"]'));
initAccordion(document.querySelector('#faq'));
initEnrollDialog();
