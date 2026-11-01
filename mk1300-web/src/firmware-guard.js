/* Verifies every firmware (.bin) the app downloads against firmware-manifest.json
 * (SHA-256, generated at build time) before the app is allowed to flash it.
 *
 * What this protects against: a corrupted or truncated download, a stale or
 * mismatched file left in a cache, and a deploy that shipped half-updated files.
 * What it does not protect against: someone who controls the web server and can
 * replace both the firmware and the manifest. Serve this app only from a host
 * you control, over HTTPS. */
(function () {
  'use strict';
  if (!window.fetch || !window.crypto || !crypto.subtle) return;

  var nativeFetch = window.fetch.bind(window);
  var manifestPromise = null;

  function loadManifest() {
    if (!manifestPromise) {
      manifestPromise = nativeFetch('./firmware-manifest.json', { cache: 'no-store' })
        .then(function (r) {
          if (!r.ok) throw new Error('firmware manifest unavailable (' + r.status + ')');
          return r.json();
        })
        .catch(function (e) {
          manifestPromise = null; // allow a retry on the next attempt
          throw e;
        });
    }
    return manifestPromise;
  }

  function toHex(buf) {
    return Array.prototype.map
      .call(new Uint8Array(buf), function (b) { return ('0' + b.toString(16)).slice(-2); })
      .join('');
  }

  function isFirmwareRequest(input) {
    try {
      var raw = typeof input === 'string' ? input : input && input.url ? input.url : String(input);
      var url = new URL(raw, location.href);
      return url.origin === location.origin && /\.bin$/i.test(url.pathname) ? url : null;
    } catch (e) {
      return null;
    }
  }

  function fail(message) {
    var err = new Error('Firmware verification failed: ' + message);
    err.name = 'FirmwareIntegrityError';
    try {
      window.dispatchEvent(new CustomEvent('mk:firmware-integrity-error', { detail: { message: message } }));
      console.error(err.message);
    } catch (e) { /* ignore */ }
    return err;
  }

  window.fetch = function (input, init) {
    var url = isFirmwareRequest(input);
    if (!url) return nativeFetch(input, init);

    var name = decodeURIComponent(url.pathname.split('/').pop());
    return Promise.all([nativeFetch(input, init), loadManifest()]).then(function (results) {
      var res = results[0];
      var manifest = results[1];
      if (!res.ok) return res; // let the app handle HTTP errors as before
      var expected = manifest && manifest.files && manifest.files[name];
      if (!expected) throw fail(name + ' is not listed in the firmware manifest');
      return res.clone().arrayBuffer().then(function (buf) {
        if (buf.byteLength !== expected.size) {
          throw fail(name + ' has size ' + buf.byteLength + ', expected ' + expected.size);
        }
        return crypto.subtle.digest('SHA-256', buf).then(function (digest) {
          if (toHex(digest) !== expected.sha256) throw fail(name + ' does not match its checksum');
          return res;
        });
      });
    });
  };
})();
