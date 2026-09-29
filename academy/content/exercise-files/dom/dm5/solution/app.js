// Lab 2.1 - Events and listeners (solution)
const LIMIT = 200;

// TODO(1): elements
const likeBtn = document.querySelector('#like');
const likeCount = document.querySelector('#like-count');
const postText = document.querySelector('#post-text');
const bigHeart = document.querySelector('#big-heart');
const form = document.querySelector('#composer');
const textarea = document.querySelector('#comment');
const counter = document.querySelector('#counter');
const postBtn = document.querySelector('#post');
const comments = document.querySelector('#comments');
const tip = document.querySelector('#tip');
const tipOk = document.querySelector('#tip-ok');
const closeBtn = document.querySelector('#close');

// TODO(2): one controller removes every listener that uses its signal
const controller = new AbortController();
const { signal } = controller;

// TODO(3): like toggle
let liked = false;
let count = Number(likeCount.textContent);

function setLiked(next) {
  if (next === liked) return;
  liked = next;
  count += liked ? 1 : -1;
  likeBtn.setAttribute('aria-pressed', String(liked));
  likeCount.textContent = count;
  likeBtn.classList.add('pop');
}

likeBtn.addEventListener('click', (event) => {
  console.log('target:', event.target.localName,
    '| currentTarget:', event.currentTarget.localName);
  setLiked(!liked);
}, { signal });

likeBtn.addEventListener('animationend', () => {
  likeBtn.classList.remove('pop');
}, { signal });

// TODO(4): double-click to like
postText.addEventListener('dblclick', () => {
  setLiked(true);
  bigHeart.classList.add('show');
}, { signal });

bigHeart.addEventListener('animationend', () => {
  bigHeart.classList.remove('show');
}, { signal });

// TODO(5): character counter
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
const countChars = (value) => [...segmenter.segment(value)].length;

function updateCounter() {
  const used = countChars(textarea.value.trim());
  const left = LIMIT - used;
  counter.textContent = left >= 0 ? `${left} left` : `${-left} over`;
  counter.classList.toggle('warn', left >= 0 && left <= 20);
  counter.classList.toggle('over', left < 0);
  postBtn.disabled = used === 0 || left < 0;
}

textarea.addEventListener('input', updateCounter, { signal });

// TODO(6): posting
form.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = textarea.value.trim();
  if (!text || countChars(text) > LIMIT) return;

  const li = document.createElement('li');
  const name = document.createElement('strong');
  name.textContent = 'You';
  li.append(name, text); // a string argument becomes a text node: safe
  comments.append(li);

  form.reset();
  updateCounter();
  textarea.focus();
}, { signal });

textarea.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    form.requestSubmit(); // fires 'submit', unlike form.submit()
  }
}, { signal });

// TODO(7): one-time tip and closing the discussion
tipOk.addEventListener('click', () => {
  tip.hidden = true;
}, { once: true });

closeBtn.addEventListener('click', () => {
  controller.abort();
  form.inert = true;
  closeBtn.disabled = true;
  closeBtn.textContent = 'Discussion closed';
  console.log('All post listeners removed with one abort()');
}, { once: true });

updateCounter();
