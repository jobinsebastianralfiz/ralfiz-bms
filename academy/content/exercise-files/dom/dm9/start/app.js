// Ralfiz Academy course page: dialog, tabs, accordion and toasts.
// The HTML and CSS are finished. Your job is the behaviour.

// ---------- toast ----------
const toastRegion = document.querySelector('#toasts');

function toast(message, { duration = 4000 } = {}) {
  // TODO(1): build <div class="toast"><p>message</p><button>✕</button></div>
  //   with createElement + textContent (never innerHTML), append it to
  //   toastRegion, remove it after `duration` ms, and let the ✕ button
  //   (aria-label "Dismiss notification") remove it early.
  // TODO(2): pause the timer on mouseenter and resume it on mouseleave
  //   (keep track of the time remaining).
  console.log('toast:', message, duration);
}

// ---------- tabs ----------
function initTabs(tablist) {
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];

  function select(tab, focus = false) {
    // TODO(3): for every tab set aria-selected ('true'/'false'),
    //   tabIndex (0 for the selected tab, -1 for the others) and the
    //   hidden property of the panel named in aria-controls.
    //   Focus the tab when focus is true.
  }

  // TODO(4): one click listener on the tablist (use closest) that calls
  //   select(), and a keydown listener for ArrowRight, ArrowLeft (both
  //   wrap around), Home and End. Call event.preventDefault() for them.
  console.log('tabs found:', tabs.length, typeof select);
}

// ---------- accordion ----------
function initAccordion(root) {
  // TODO(5): one delegated click listener. Toggle aria-expanded on the
  //   .acc-btn and the hidden property of its panel (aria-controls).
  console.log('accordion ready:', root.id);
}

// ---------- enroll dialog ----------
function initEnrollDialog() {
  const dialog = document.querySelector('#enroll');
  const openBtn = document.querySelector('#enroll-btn');

  // TODO(6): the "Reserve a seat" button resets the form, clears
  //   dialog.returnValue and calls dialog.showModal().
  //   The Cancel button ([data-close]) calls dialog.close('cancel'),
  //   and a click whose target is the dialog itself (the backdrop) too.
  // TODO(7): on the dialog's close event, move focus back to openBtn.
  //   If returnValue is 'enroll', read the form with FormData and show
  //   toast(`Seat reserved for NAME (BATCH). Check EMAIL.`)
  console.log('dialog found:', Boolean(dialog), Boolean(openBtn));
}

initTabs(document.querySelector('[role="tablist"]'));
initAccordion(document.querySelector('#faq'));
initEnrollDialog();
