/* Accessibility fixes for the exported UI, applied without modifying its bundle.
 * Remove this file once the original source is fixed (see README, "Known gaps"). */
(function () {
  'use strict';

  // Known images get a real description; anything else is treated as decorative.
  var ALT = {
    'home_device.png': 'Illustration of the MK1300 V2 keyboard plugged into a USB cable',
  };

  function fixImage(img) {
    if (img.hasAttribute('alt')) return;
    var file = (img.getAttribute('src') || '').split('/').pop().split('?')[0];
    img.setAttribute('alt', ALT[file] || '');
  }

  function scan(root) {
    if (root.nodeType !== 1) return;
    if (root.tagName === 'IMG') fixImage(root);
    var imgs = root.getElementsByTagName ? root.getElementsByTagName('img') : [];
    for (var i = 0; i < imgs.length; i++) fixImage(imgs[i]);
  }

  // The UI shrinks itself on phones by setting maximum-scale=0.6 from its own
  // code. That blocks pinch/browser zoom (WCAG 1.4.4) and does nothing on the
  // desktop browsers WebHID works in, so take it out whenever it appears.
  function fixViewport() {
    var metas = document.querySelectorAll('meta[name="viewport"]');
    for (var i = 0; i < metas.length; i++) {
      var c = metas[i].getAttribute('content') || '';
      var fixed = c.replace(/,?\s*maximum-scale=[0-9.]+/g, '').replace(/,?\s*user-scalable=no/g, '');
      if (fixed !== c) metas[i].setAttribute('content', fixed);
    }
  }

  function init() {
    scan(document.documentElement);
    fixViewport();
    new MutationObserver(function (records) {
      var viewportTouched = false;
      for (var i = 0; i < records.length; i++) {
        if (records[i].type === 'attributes') { viewportTouched = true; continue; }
        for (var j = 0; j < records[i].addedNodes.length; j++) scan(records[i].addedNodes[j]);
        viewportTouched = true;
      }
      if (viewportTouched) fixViewport();
    }).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['content'] });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
