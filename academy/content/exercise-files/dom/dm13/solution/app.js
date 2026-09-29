// Ralfiz Academy: a history (pushState) router. Loaded as a module.

// The folder this app is served from, e.g. '/' or '/dom/dm13/solution/'
const BASE = new URL('.', import.meta.url).pathname;
const toUrl = (path) => BASE + path.slice(1);            // '/courses' → BASE + 'courses'
function currentPath() {
  const rest = '/' + location.pathname.slice(BASE.length);
  return rest === '/index.html' ? '/' : rest;
}

const COURSES = [
  { id: 'js', icon: '🟨', name: 'JavaScript: Zero to Job-Ready', lessons: 31, level: 'Beginner' },
  { id: 'dom', icon: '🧩', name: 'DOM & Browser', lessons: 24, level: 'Beginner' },
  { id: 'flutter', icon: '🦋', name: 'Flutter Apps', lessons: 40, level: 'Intermediate' },
  { id: 'pbi', icon: '📊', name: 'Power BI in Practice', lessons: 18, level: 'Beginner' },
  { id: 'ts', icon: '🔷', name: 'TypeScript Deep Dive', lessons: 22, level: 'Advanced' },
];
const LEVELS = ['All', 'Beginner', 'Intermediate', 'Advanced'];

function h(tag, { dataset, ...props } = {}, ...kids) {
  const el = Object.assign(document.createElement(tag), props);
  if (dataset) Object.assign(el.dataset, dataset);
  el.append(...kids);
  return el;
}
const link = (to, text, props = {}) =>
  h('a', { ...props, href: toUrl(to), dataset: { to } }, text);

// ---- views ----
const home = () => h('section', {},
  h('h1', {}, 'Learn by building'),
  h('p', { className: 'lead' }, 'Short lessons, live code and real projects.'),
  link('/courses', 'Browse courses', { className: 'btn' }),
  h('h2', { className: 'sub' }, 'Popular this month'),
  h('div', { className: 'grid' }, ...COURSES.slice(0, 3).map(courseCard)));

function courses() {
  const asked = new URLSearchParams(location.search).get('level');
  const level = LEVELS.includes(asked) ? asked : 'All';     // validate URL input
  const list = COURSES.filter((c) => level === 'All' || c.level === level);
  const chips = h('div', { className: 'chips' }, ...LEVELS.map((l) => {
    const a = link(l === 'All' ? '/courses' : '/courses?level=' + l, l);
    a.dataset.replace = '';                                 // filters replace
    a.setAttribute('aria-current', String(l === level));
    return a;
  }));
  return h('section', {}, h('h1', {}, 'Courses'),
    h('p', { className: 'lead' }, list.length + ' courses'),
    chips, h('div', { className: 'grid' }, ...list.map(courseCard)));
}
const courseCard = (c) => {
  const a = link('/courses/' + c.id, '', { className: 'course' });
  a.append(h('span', { className: 'ico' }, c.icon), h('h2', {}, c.name),
    h('p', {}, c.lessons + ' lessons · ' + c.level));
  return a;
};

function course({ id }) {
  const c = COURSES.find((x) => x.id === id);
  if (!c) return notFound();
  return h('section', {}, h('h1', {}, c.icon + ' ' + c.name),
    h('p', {}, h('span', { className: 'pill' }, c.level),
      h('span', { className: 'pill' }, c.lessons + ' lessons')),
    link('/courses', '← All courses'));
}
const about = () => h('section', {}, h('h1', {}, 'About'),
  h('p', { className: 'lead' }, 'Ralfiz Academy is the training arm of Ralfiz Technologies.'));
const notFound = () => h('section', {}, h('h1', {}, 'Page not found'),
  h('p', { className: 'lead' }, 'Nothing lives at ' + currentPath()), link('/', 'Go home'));

// ---- router ----
const routes = [
  { path: '/', view: home, title: 'Home' },
  { path: '/courses', view: courses, title: 'Courses' },
  { path: '/courses/:id', view: course, title: 'Course' },
  { path: '/about', view: about, title: 'About' },
];

function compile(path) {
  const keys = [];
  const source = path.replace(/:(\w+)/g, (_, key) => {
    keys.push(key);
    return '([^/]+)';
  });
  return { re: new RegExp('^' + source + '$'), keys };
}
routes.forEach((r) => Object.assign(r, compile(r.path)));

function match(pathname) {
  for (const route of routes) {
    const m = pathname.match(route.re);
    if (!m) continue;
    const params = Object.fromEntries(
      route.keys.map((key, i) => [key, decodeURIComponent(m[i + 1])]));
    return { route, params };
  }
  return null;
}

function render() {
  const path = currentPath();
  const found = match(path);
  const view = document.querySelector('#view');
  view.replaceChildren(found ? found.route.view(found.params) : notFound());
  document.title = (found?.route.title ?? 'Not found') + ' · Ralfiz Academy';
  document.querySelectorAll('[data-nav]').forEach((a) => {
    const here = a.dataset.to === '/' ? path === '/' : path.startsWith(a.dataset.to);
    if (here) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  view.focus({ preventScroll: true });
  scrollTo(0, 0);
}

function navigate(path, { replace = false } = {}) {
  const url = toUrl(path);
  if (url === location.pathname + location.search) return;  // no duplicate entry
  history[replace ? 'replaceState' : 'pushState']({}, '', url);
  render();
}

document.addEventListener('click', (event) => {
  const a = event.target.closest('a[data-to]');
  if (!a) return;
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  navigate(a.dataset.to, { replace: 'replace' in a.dataset });
});

addEventListener('popstate', render);

document.querySelectorAll('a[data-to]').forEach((a) => { a.href = toUrl(a.dataset.to); });
render();
console.log('Router ready at base', BASE);
