/* Runs before the app. Checks that this browser can reach a USB keyboard and, if
 * not, covers the page with a clear explanation instead of a dead button. */
(function () {
  'use strict';

  var ua = navigator.userAgent || '';
  var isSafari = /^((?!chrome|chromium|android|crios|fxios|edg).)*safari/i.test(ua);
  var isFirefox = /firefox|fxios/i.test(ua);
  var isMobile = /android|iphone|ipad|ipod|mobile/i.test(ua);

  var reason = null;
  if (!window.isSecureContext) {
    reason = {
      title: 'This page needs a secure connection',
      body:
        'Your browser only lets websites talk to USB devices over HTTPS. ' +
        'Open this app using its https:// address.',
    };
  } else if (!('hid' in navigator)) {
    var who = isSafari ? 'Safari' : isFirefox ? 'Firefox' : isMobile ? 'Mobile browsers' : 'This browser';
    reason = {
      title: who + " can't connect to your keyboard",
      body:
        'Keyboard configuration uses WebHID, which only desktop Chrome, Edge and ' +
        'other Chromium browsers provide. Open this page in one of those to continue.',
    };
  }

  if (!reason) return;

  document.documentElement.setAttribute('data-unsupported', '');

  function render() {
    var root = document.createElement('div');
    root.className = 'mk-gate';
    root.setAttribute('role', 'alertdialog');
    root.setAttribute('aria-modal', 'true');
    root.setAttribute('aria-labelledby', 'mk-gate-title');
    root.setAttribute('aria-describedby', 'mk-gate-body');

    var card = document.createElement('div');
    card.className = 'mk-gate__card';

    var h = document.createElement('h1');
    h.id = 'mk-gate-title';
    h.className = 'mk-gate__title';
    h.tabIndex = -1;
    h.textContent = reason.title;

    var p = document.createElement('p');
    p.id = 'mk-gate-body';
    p.className = 'mk-gate__body';
    p.textContent = reason.body;

    var list = document.createElement('ul');
    list.className = 'mk-gate__list';
    ['Google Chrome', 'Microsoft Edge', 'Brave, Opera, Arc and other Chromium browsers'].forEach(function (t) {
      var li = document.createElement('li');
      li.textContent = t;
      list.appendChild(li);
    });

    var actions = document.createElement('div');
    actions.className = 'mk-gate__actions';

    var copy = document.createElement('button');
    copy.type = 'button';
    copy.className = 'mk-gate__button';
    copy.textContent = 'Copy page address';
    var status = document.createElement('span');
    status.className = 'mk-gate__status';
    status.setAttribute('role', 'status');
    copy.addEventListener('click', function () {
      var done = function (ok) {
        status.textContent = ok ? 'Copied. Paste it into Chrome or Edge.' : 'Copy failed. Select the address bar and copy it.';
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(location.href).then(function () { done(true); }, function () { done(false); });
      } else {
        done(false);
      }
    });

    var link = document.createElement('a');
    link.className = 'mk-gate__link';
    link.href = 'https://www.google.com/chrome/';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Get Chrome';

    actions.appendChild(copy);
    actions.appendChild(link);
    card.appendChild(h);
    card.appendChild(p);
    card.appendChild(list);
    card.appendChild(actions);
    card.appendChild(status);
    root.appendChild(card);
    // Mounted next to <body>, not inside it, so the whole app (including
    // anything it adds later) can be made inert without affecting the dialog.
    document.documentElement.appendChild(root);

    // The app underneath cannot work here; take it out of the tab order and
    // the accessibility tree so keyboard and screen-reader users stay in the dialog.
    document.body.inert = true;
    h.focus();
  }

  if (document.body) render();
  else document.addEventListener('DOMContentLoaded', render);
})();
