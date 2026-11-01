/* Registers the offline-capable service worker. Skipped on insecure origins and
 * when the URL contains ?nosw (useful for debugging a stale cache). */
(function () {
  'use strict';
  if (!('serviceWorker' in navigator) || !window.isSecureContext) return;
  if (/[?&]nosw\b/.test(location.search)) return;
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('./sw.js', { scope: './' }).catch(function (e) {
      console.warn('Service worker not registered:', e && e.message);
    });
  });
})();
