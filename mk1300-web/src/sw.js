/* Service worker. The build id and the precache list below are filled in by
 * scripts/build.mjs at build time. */
const BUILD = '__BUILD_ID__';
const CORE = __PRECACHE__;
const STATIC_CACHE = 'mk1300-static-' + BUILD;
const RUNTIME_CACHE = 'mk1300-runtime-v1';

// Anything that decides what gets flashed to the keyboard must never come from a
// cache: a stale firmware file or manifest is worse than being offline.
const NEVER_CACHE = (path) =>
  /\.bin$/i.test(path) ||
  path.endsWith('/update.json') ||
  path.endsWith('/firmware-manifest.json') ||
  path.endsWith('/sw.js');

self.addEventListener('install', (event) => {
  // No skipWaiting: a new version waits until every open tab is closed, so a
  // running session (possibly mid-configuration) is never swapped underneath.
  event.waitUntil(caches.open(STATIC_CACHE).then((cache) => cache.addAll(CORE)));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k.startsWith('mk1300-static-') && k !== STATIC_CACHE)
            .map((k) => caches.delete(k))
        )
      )
  );
});

async function cachePut(cacheName, request, response) {
  if (response && response.ok && response.type === 'basic') {
    const cache = await caches.open(cacheName);
    await cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request) {
  try {
    return await cachePut(RUNTIME_CACHE, request, await fetch(request));
  } catch (e) {
    const cached = (await caches.match(request)) || (await caches.match('./index.html'));
    if (cached) return cached;
    throw e;
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  return cached || cachePut(STATIC_CACHE, request, await fetch(request));
}

async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  const refresh = fetch(request)
    .then((res) => cachePut(RUNTIME_CACHE, request, res))
    .catch(() => cached);
  return cached || refresh;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (NEVER_CACHE(url.pathname)) return; // straight to the network

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
  } else if (url.pathname.includes('/_next/static/')) {
    event.respondWith(cacheFirst(request));
  } else {
    event.respondWith(staleWhileRevalidate(request));
  }
});
