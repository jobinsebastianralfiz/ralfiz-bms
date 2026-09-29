const $ = (sel) => document.querySelector(sel);
const statusEl = $('#status');
const say = (msg) => { statusEl.textContent = msg; };

const deal = {
  title: 'Ralfiz Deals',
  text: 'Flat 20% off headphones with RALFIZ20',
  url: 'https://shop.ralfiz.dev/deals/headphones',
};
const DEAL_ENDS = Date.now() + 1000 * 60 * 60 * 26; // demo: 26 hours from now
const STORES = [
  { name: 'Ralfiz Store Kochi', lat: 9.9312, lon: 76.2673 },
  { name: 'Ralfiz Store Kozhikode', lat: 11.2588, lon: 75.7804 },
  { name: 'Ralfiz Store Bengaluru', lat: 12.9716, lon: 77.5946 },
];

function renderStores(list) {
  $('#stores').replaceChildren(...list.map((s) => {
    const li = document.createElement('li');
    li.textContent = s.name;
    if (s.km !== undefined) {
      const small = document.createElement('small');
      small.textContent = s.km.toFixed(0) + ' km';
      li.append(small);
    }
    return li;
  }));
}
renderStores(STORES);

// TODO(1): try navigator.clipboard.writeText, fall back to selecting #code.
// Return 'copied' or 'selected'.
async function copyText(text) {
  return 'selected';
}
$('#copy').addEventListener('click', async () => {
  const result = await copyText($('#code').value);
  say(result === 'copied' ? 'Code copied.' : 'Press Ctrl+C to copy the selected code.');
});

// TODO(2): Share button (Web Share with an AbortError check, else copy deal.url)

// TODO(3): theme from localStorage choice + matchMedia, live updates
function applyTheme() {}
applyTheme();

// TODO(4): offline banner and disabled Claim button

// TODO(5): countdown that is computed from DEAL_ENDS and pauses while hidden
function formatLeft(ms) {
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return h + 'h ' + String(m).padStart(2, '0') + 'm ' + String(s).padStart(2, '0') + 's';
}

// TODO(6): #find uses geolocation (codes 1, 2, 3); #alerts asks for notifications
console.log('Ralfiz Deals starter loaded');
