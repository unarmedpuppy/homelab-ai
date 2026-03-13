// Minimal service worker — network-first passthrough for PWA installability
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});
