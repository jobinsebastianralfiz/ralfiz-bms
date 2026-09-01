{% load static %}/* Ralfiz Staff service worker.
 *
 * Deliberately conservative: the shell is cached so the app opens instantly and
 * shows a useful screen with no signal, but nothing that decides attendance is
 * ever served from cache, and no write is ever queued offline -- check-in time
 * must come from the server, not from a replayed request.
 */
const CACHE = 'ralfiz-staff-v1';

const SHELL = [
  '{% static "css/staff.css" %}',
  '{% static "js/staff.js" %}',
  '{% static "staff/icon-192.png" %}',
  '/staff/offline/'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Only ever touch our own GETs. Writes and cross-origin go straight to the network.
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;

  // Never cache the API -- attendance state must always be live.
  if (new URL(req.url).pathname.startsWith('/api/')) return;

  // Pages: network first, fall back to the offline card.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() => caches.match('/staff/offline/'))
    );
    return;
  }

  // Static assets: cache first, refill in the background.
  event.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      if (res && res.status === 200 && res.type === 'basic') {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    }))
  );
});
