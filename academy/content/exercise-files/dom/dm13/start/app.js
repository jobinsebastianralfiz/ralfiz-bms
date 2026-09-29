// Ralfiz Academy: a history (pushState) router. Loaded as a module.

// The folder this app is served from, e.g. '/' or '/dom/dm13/start/'
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
  // TODO(6): read ?level= with URLSearchParams(location.search), check it
  // against LEVELS, and filter the list. Render LEVELS as chips (links to
  // '/courses?level=...') and navigate with { replace: true } when clicked.
  return h('section', {}, h('h1', {}, 'Courses'),
    h('div', { className: 'grid' }, ...COURSES.map(courseCard)));
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
  // TODO(1): replace each :name with ([^/]+), remember the names in keys,
  // and return { re: new RegExp('^' + source + '$'), keys }.
  return { re: new RegExp('^' + path + '$'), keys: [] };
}
routes.forEach((r) => Object.assign(r, compile(r.path)));

function match(pathname) {
  // TODO(2): find the first route whose re matches pathname and return
  // { route, params } (params built from keys and the capture groups).
  return pathname === '/' ? { route: routes[0], params: {} } : null;
}

function render() {
  // TODO(3): match currentPath(), put the view in #view (replaceChildren),
  // set document.title and aria-current="page" on the matching [data-nav].
  const found = match(currentPath());
  document.querySelector('#view').replaceChildren((found?.route.view ?? home)({}));
  // TODO(7): move focus to #view and scroll to the top.
}

function navigate(path, { replace = false } = {}) {
  const url = toUrl(path);
  if (url === location.pathname + location.search) return;
  history[replace ? 'replaceState' : 'pushState']({}, '', url);
  render();
}

// TODO(4): one click listener on document for a[data-to]. Skip modified clicks
// (event.button !== 0, metaKey, ctrlKey, shiftKey), preventDefault, navigate().

// TODO(5): re-render on popstate (Back / Forward).

document.querySelectorAll('a[data-to]').forEach((a) => { a.href = toUrl(a.dataset.to); });
render();
