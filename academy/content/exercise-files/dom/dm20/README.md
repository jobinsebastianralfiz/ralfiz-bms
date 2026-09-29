# Lab 5.3 - Secure the Ralfiz comments widget

The widget in `start/` works, but it is full of classic front-end security bugs.
Find them, prove them with a harmless payload, then fix them in layers.

## Run it

In a terminal inside `dom/dm20/start` run `npx serve` and open the printed URL.
(VS Code Live Server also works, but it injects an inline reload script, which your
Content Security Policy will block once you add it. That is the CSP doing its job.)

## Prove the bug (harmless payload)

Post this comment in the starter:

    <img src=x onerror="console.log('XSS ran')">

The console logs "XSS ran": attacker code executed. A real attacker would read
localStorage and send it away.

## Tasks

- TODO(1) `renderComment()`: createElement + textContent only.
- TODO(2) `safeUrl()`: new URL() + an allowlist of https: and http:; rel="noopener noreferrer".
- TODO(3) Allow <b>, <i>, <code> with DOMPurify
  (`ALLOWED_TAGS: ['b', 'i', 'code'], ALLOWED_ATTR: []`). If DOMPurify failed to load,
  fall back to textContent: fail closed.
- TODO(4) A CSP meta tag in `index.html`.
- TODO(5) Remove the fake `PAYMENTS_SECRET`.
- TODO(6) Stop keeping the session token in localStorage.

## Production notes

- Pin DOMPurify to an exact version and add `integrity` + `crossorigin="anonymous"`
  (Subresource Integrity), or install it with `npm install dompurify`.
- Send CSP as an HTTP header so you can also use `frame-ancestors 'none'`.
- `script-src https://cdn.jsdelivr.net` trusts every file on that CDN, so an
  injected script tag could load any package from it. In production self-host
  DOMPurify, list its exact file URL in script-src, or use nonces.

## Acceptance criteria

- The payload above appears as text and nothing is logged.
- `Loved it <b>so much</b>` shows "so much" in bold when DOMPurify is loaded.
- A website of `javascript:alert(1)` shows no link; `https://anu.ralfiz.dev` shows one.
- `localStorage` contains only the comments, never a token.
- DevTools > Sources: searching for "sk_" finds nothing.
