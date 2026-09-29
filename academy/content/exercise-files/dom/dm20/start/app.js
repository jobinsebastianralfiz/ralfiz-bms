// TODO(5): a secret in front-end code is public. Remove it.
const PAYMENTS_SECRET = 'sk_live_FAKE_DO_NOT_SHIP_123';

// TODO(6): any XSS can read this. Do not keep tokens in localStorage.
localStorage.setItem('sessionToken', 'demo-token-abc');

const seed = [
  { name: 'Anu', site: 'https://anu.ralfiz.dev', body: 'Loved it <b>so much</b>!' },
  { name: 'Rahul', site: '', body: 'Use <code>textContent</code> by default.' },
];
const comments = JSON.parse(localStorage.getItem('comments') ?? 'null') ?? seed;
const list = document.querySelector('#comments');

// TODO(2): validate the website with new URL() and a protocol allowlist
function safeUrl(input) {
  return input;
}

// TODO(1): this puts user data into innerHTML. Rebuild it with createElement/textContent.
// TODO(3): allow <b>, <i>, <code> only, via DOMPurify.
function renderComment(c) {
  const li = document.createElement('li');
  li.className = 'comment';
  li.innerHTML = `
    <div class="meta"><strong>${c.name}</strong>
      ${c.site ? `<a href="${safeUrl(c.site)}" target="_blank">website</a>` : ''}</div>
    <p class="body">${c.body}</p>`;
  return li;
}

function render() {
  list.replaceChildren(...comments.map(renderComment));
}

document.querySelector('#form').addEventListener('submit', (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  comments.unshift({ name: data.name, site: data.site.trim(), body: data.body });
  localStorage.setItem('comments', JSON.stringify(comments));
  event.target.reset();
  render();
});

function checkout() {
  // Pretend payment call that uses the secret from the browser (never do this)
  return { key: PAYMENTS_SECRET.slice(0, 7) + '…' };
}

render();
console.log('Comments loaded:', comments.length, '| checkout config', checkout());
