# dm13 lab: Ralfiz Academy with a history router

Build a small multi-page site that runs from ONE index.html. Clean URLs such as
/courses and /courses/js are handled in the browser with history.pushState.

## Run it
A history router needs a server with an SPA fallback (every unknown path returns index.html).

    cd dom/dm13/start      # or dom/dm13/solution
    npx serve -s .         # -s = single-page app fallback

Open the address that serve prints (usually http://localhost:3000).
VS Code Live Server also works for clicking around, but it has no fallback,
so refreshing on /courses shows its 404 page. That is the bug the fallback fixes.

The router works out its base folder from import.meta.url, so it also runs
when the folder is served from a sub-path.

## Tasks
Work through TODO(1) to TODO(7) in app.js. The steps are in the lesson.

## Acceptance criteria
- Clicking Home, Courses, About and a course card changes the address bar
  without a page reload (the Network panel shows no new document request).
- Back and Forward move between the pages you visited.
- /courses?level=Intermediate shows only intermediate courses, and clicking a
  level chip updates ?level= without adding a history entry.
- An unknown path such as /nope shows the "Page not found" view.
- The browser tab title and the highlighted nav link follow the page.
- With npx serve -s, refreshing on /courses or /about shows the same page.

## Think about it
Refresh on /courses/js. The page is served, but app.js is requested as
/courses/app.js. Why? Fix it by changing the two asset paths in index.html
to root-absolute paths (/style.css and /app.js) when this folder is the site
root. This is exactly why real SPAs use absolute asset URLs or a <base href="/">.
