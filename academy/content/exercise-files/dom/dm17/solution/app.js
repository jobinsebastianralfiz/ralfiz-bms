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

// 1. Clipboard with a fallback
async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return 'copied';
    } catch (err) {
      console.warn('Clipboard refused:', err.name);
    }
  }
  $('#code').focus();
  $('#code').select();
  return 'selected';
}
$('#copy').addEventListener('click', async () => {
  const result = await copyText($('#code').value);
  say(result === 'copied' ? 'Code copied.' : 'Press Ctrl+C to copy the selected code.');
});

// 2. Web Share with a copy-link fallback
$('#share').addEventListener('click', async () => {
  if (typeof navigator.share === 'function') {
    try {
      await navigator.share(deal);
      return say('Thanks for sharing!');
    } catch (err) {
      if (err.name === 'AbortError') return; // the user closed the sheet
    }
  }
  const result = await copyText(deal.url);
  say(result === 'copied' ? 'Link copied.' : 'Sharing is not available here.');
});

// 3. Theme: saved choice + system preference
const darkQuery = matchMedia('(prefers-color-scheme: dark)');
let choice = localStorage.getItem('theme') ?? 'system';
function applyTheme() {
  const dark = choice === 'dark' || (choice === 'system' && darkQuery.matches);
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  document.querySelectorAll('[data-choice]').forEach((b) => {
    b.setAttribute('aria-pressed', String(b.dataset.choice === choice));
  });
}
$('.seg').addEventListener('click', (event) => {
  const btn = event.target.closest('[data-choice]');
  if (!btn) return;
  choice = btn.dataset.choice;
  localStorage.setItem('theme', choice);
  applyTheme();
});
darkQuery.addEventListener('change', applyTheme);
applyTheme();

// 4. Network state
function renderNetwork() {
  const online = navigator.onLine;
  $('#offline').hidden = online;
  $('#claim').disabled = !online;
}
addEventListener('online', renderNetwork);
addEventListener('offline', renderNetwork);
renderNetwork();
$('#claim').addEventListener('click', () => say('Deal claimed! Check your email.'));

// 5. Countdown computed from the end time; no DOM work while hidden
function formatLeft(ms) {
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return h + 'h ' + String(m).padStart(2, '0') + 'm ' + String(s).padStart(2, '0') + 's';
}
function tick() {
  if (document.visibilityState === 'hidden') return;
  $('#countdown').textContent = formatLeft(Math.max(0, DEAL_ENDS - Date.now()));
}
setInterval(tick, 1000);
document.addEventListener('visibilitychange', tick);
tick();

// 6a. Geolocation, promise-wrapped
function getPosition() {
  return new Promise((resolve, reject) => {
    if (!('geolocation' in navigator)) return reject({ code: 0, message: 'Not supported' });
    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000, maximumAge: 60000 });
  });
}
function distanceKm(lat1, lon1, lat2, lon2) {
  const rad = (d) => (d * Math.PI) / 180;
  const a = Math.sin(rad(lat2 - lat1) / 2) ** 2 +
    Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(rad(lon2 - lon1) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(a));
}
$('#find').addEventListener('click', async () => {
  say('Finding you…');
  try {
    const { coords } = await getPosition();
    const sorted = STORES
      .map((s) => ({ ...s, km: distanceKm(coords.latitude, coords.longitude, s.lat, s.lon) }))
      .toSorted((a, b) => a.km - b.km);
    renderStores(sorted);
    say('Nearest: ' + sorted[0].name);
  } catch (err) {
    const reasons = { 1: 'Location blocked', 2: 'Location unavailable', 3: 'Timed out' };
    say((reasons[err.code] ?? err.message) + '. Pick a store from the list.');
  }
});

// 6b. Notifications, asked in context
$('#alerts').addEventListener('click', async () => {
  if (!('Notification' in window)) return say('Notifications are not supported here.');
  if (Notification.permission === 'denied') return say('Alerts are blocked in site settings.');
  const result = await Notification.requestPermission();
  if (result !== 'granted') return say('No problem, no alerts.');
  try {
    new Notification('Ralfiz Deals', { body: 'We will tell you when prices drop.' });
  } catch {
    say('Alerts on (mobile needs a service worker to show them).');
  }
});
