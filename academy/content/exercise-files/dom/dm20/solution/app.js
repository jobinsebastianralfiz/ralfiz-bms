// 5. No secrets here. The browser calls our backend (e.g. POST /api/checkout),
//    and only the server knows the payment provider's secret key.

// 6. The session lives in an HttpOnly; Secure; SameSite=Lax cookie set by the server,
//    which page scripts cannot read. Anything short-lived we need stays in memory:
let accessToken = null; // never written to localStorage
localStorage.removeItem('sessionToken'); // clean up what the old version stored

const seed = [
  { name: 'Anu', site: 'https://anu.ralfiz.dev', body: 'Loved it <b>so much</b>!' },
  { name: 'Rahul', site: '', body: 'Use <code>textContent</code> by default.' },
];
const comments = JSON.parse(localStorage.getItem('comments') ?? 'null') ?? seed;
const list = document.querySelector('#comments');

// 2. Allowlist of protocols, checked on the parsed URL
function safeUrl(input) {
  try {
    const url = new URL(input.trim());
    return ['https:', 'http:'].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

// 3. Limited formatting; fail closed if the sanitiser is missing
function renderBody(el, body) {
  if (window.DOMPurify) {
    el.innerHTML = DOMPurify.sanitize(body, { ALLOWED_TAGS: ['b', 'i', 'code'], ALLOWED_ATTR: [] });
  } else {
    el.textContent = body;
  }
}

// 1. Structure from code, data as text
function renderComment(c) {
  const li = document.createElement('li');
  li.className = 'comment';
  const meta = document.createElement('div');
  meta.className = 'meta';
  const name = document.createElement('strong');
  name.textContent = c.name;
  meta.append(name);
  const href = c.site ? safeUrl(c.site) : null;
  if (href) {
    const a = document.createElement('a');
    a.href = href;
    a.textContent = new URL(href).host;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    meta.append(a);
  }
  const body = document.createElement('p');
  body.className = 'body';
  renderBody(body, c.body);
  li.append(meta, body);
  return li;
}

function render() {
  list.replaceChildren(...comments.map(renderComment));
}

document.querySelector('#form').addEventListener('submit', (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  comments.unshift({ name: data.name.trim(), site: data.site.trim(), body: data.body });
  localStorage.setItem('comments', JSON.stringify(comments.slice(0, 50)));
  event.target.reset();
  render();
});

render();
console.log('Comments loaded:', comments.length,
  '| sanitiser:', window.DOMPurify ? 'DOMPurify' : 'not loaded, using text',
  '| token in memory:', accessToken !== null);
