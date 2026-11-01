#!/usr/bin/env node
/* End-to-end tests against the built site, in real Chromium with a stubbed
 * WebHID (there is no keyboard in CI). Run with: npm test
 * Set CHROMIUM_PATH to use a specific Chromium binary. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { start } from '../scripts/serve.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const HID_STUB = () => {
  Object.defineProperty(navigator, 'hid', {
    configurable: true,
    value: { getDevices: async () => [], requestDevice: async () => [], addEventListener() {}, removeEventListener() {} },
  });
};
const CSP_SPY = () => {
  window.__csp = [];
  document.addEventListener('securitypolicyviolation', (e) =>
    window.__csp.push(`${e.violatedDirective} blocked ${e.blockedURI}`)
  );
};

const results = [];
async function test(name, fn, timeoutMs = 60000) {
  try {
    let timer;
    await Promise.race([
      fn(),
      new Promise((_, rej) => { timer = setTimeout(() => rej(new Error(`timed out after ${timeoutMs / 1000}s`)), timeoutMs); }),
    ]).finally(() => clearTimeout(timer));
    results.push({ name, ok: true });
    console.log(`  ok    ${name}`);
  } catch (e) {
    results.push({ name, ok: false, error: e });
    console.log(`  FAIL  ${name}\n        ${String(e.message).split('\n').join('\n        ')}`);
  }
}

const { server, url } = await start(0);
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });

async function open(opts = {}, { hid = true } = {}) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, serviceWorkers: 'block', ...opts });
  const page = await context.newPage();
  const problems = [];
  page.on('pageerror', (e) => problems.push('pageerror: ' + e.message));
  page.on('console', (m) => m.type() === 'error' && problems.push('console: ' + m.text()));
  await page.addInitScript(CSP_SPY);
  if (hid) await page.addInitScript(HID_STUB);
  return { context, page, problems };
}

console.log(`\nTesting ${url}\n`);

await test('security headers are present on pages and assets', async () => {
  for (const p of ['/', '/index.html', '/manifest.webmanifest', '/3key_v104.bin']) {
    const res = await fetch(url + p);
    assert.equal(res.status, 200, `${p} status`);
    const h = res.headers;
    assert.match(h.get('content-security-policy'), /default-src 'self'/, `${p} CSP`);
    assert.match(h.get('content-security-policy'), /frame-ancestors 'none'/);
    assert.match(h.get('content-security-policy'), /object-src 'none'/);
    assert.doesNotMatch(h.get('content-security-policy'), /script-src[^;]*unsafe-inline/, 'scripts must not allow unsafe-inline');
    assert.doesNotMatch(h.get('content-security-policy'), /unsafe-eval/);
    assert.match(h.get('permissions-policy'), /hid=\(self\)/);
    assert.equal(h.get('x-content-type-options'), 'nosniff');
    assert.equal(h.get('x-frame-options'), 'DENY');
    assert.equal(h.get('cross-origin-opener-policy'), 'same-origin');
  }
});

await test('cache policy: firmware and manifests are never cached, hashed assets are immutable', async () => {
  for (const p of ['/', '/update.json', '/firmware-manifest.json', '/3key_v104.bin', '/sw.js']) {
    assert.match((await fetch(url + p)).headers.get('cache-control'), /no-cache/, p);
  }
  const html = await (await fetch(url + '/')).text();
  const chunk = html.match(/\.\/(_next\/static\/chunks\/[^"]+\.js)/)[1];
  assert.match((await fetch(`${url}/${chunk}`)).headers.get('cache-control'), /immutable/);
});

await test('supported browser: app loads with no errors and no CSP violations', async () => {
  const { context, page, problems } = await open();
  await page.goto(url + '/');
  await page.getByText('Welcome to Keyboard HUB').waitFor();
  await page.getByRole('button', { name: /initialise device/i }).waitFor();
  assert.equal(await page.locator('.mk-gate').count(), 0, 'gate must not show');
  assert.equal(await page.evaluate(() => document.documentElement.lang), 'en');
  assert.ok((await page.title()).includes('MK1300'), 'has a title');
  assert.deepEqual(await page.evaluate(() => window.__csp), [], 'CSP violations');
  assert.deepEqual(problems, []);
  await context.close();
});

await test('unsupported browser (no WebHID): gate is shown, accessible, and blocks the app', async () => {
  const { context, page } = await open({}, { hid: false });
  await page.addInitScript(() => { delete Navigator.prototype.hid; });
  await page.goto(url + '/');
  const gate = page.getByRole('alertdialog');
  await gate.waitFor();
  assert.match(await gate.innerText(), /WebHID/);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'mk-gate-title', 'focus moves into the dialog');
  assert.equal(await page.evaluate(() => document.body.inert), true, 'app content is inert behind the dialog');
  assert.equal(await page.evaluate(() => document.querySelector('.mk-gate').inert), false, 'dialog itself stays interactive');
  await page.getByRole('button', { name: /copy page address/i }).waitFor();
  await context.close();
});

await test('Safari gets a Safari-specific message', async () => {
  const { context, page } = await open(
    { userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15' },
    { hid: false }
  );
  await page.addInitScript(() => { delete Navigator.prototype.hid; });
  await page.goto(url + '/');
  assert.match(await page.getByRole('alertdialog').innerText(), /Safari can't connect/);
  await context.close();
});

await test('firmware guard: valid firmware passes, tampered/unknown/truncated firmware is rejected', async () => {
  const { context, page } = await open();
  await page.goto(url + '/');
  await page.getByText('Welcome to Keyboard HUB').waitFor();
  const good = await page.evaluate(async () => (await (await fetch('./3key_v104.bin')).arrayBuffer()).byteLength);
  const real = (await readFile(path.join(ROOT, 'dist/3key_v104.bin'))).length;
  assert.equal(good, real);

  const attempt = (file) =>
    page.evaluate(async (f) => {
      try { await fetch(f); return 'resolved'; } catch (e) { return e.name; }
    }, file);

  await page.route('**/4key_v104.bin', (r) => r.fulfill({ status: 200, body: Buffer.alloc(32768, 7) })); // same size, wrong bytes
  assert.equal(await attempt('./4key_v104.bin'), 'FirmwareIntegrityError', 'tampered bytes');
  await page.route('**/6key_v104.bin', (r) => r.fulfill({ status: 200, body: Buffer.alloc(100) })); // truncated
  assert.equal(await attempt('./6key_v104.bin'), 'FirmwareIntegrityError', 'truncated');
  await page.route('**/evil.bin', (r) => r.fulfill({ status: 200, body: Buffer.alloc(10) }));
  assert.equal(await attempt('./evil.bin'), 'FirmwareIntegrityError', 'unlisted file');
  assert.equal(await page.evaluate(async () => (await fetch('./update.json')).status), 200, 'non-firmware fetches untouched');
  await context.close();
});

await test('service worker: installs, works offline, and never caches firmware or manifests', async () => {
  const { context, page } = await open({ serviceWorkers: 'allow' });
  await page.goto(url + '/');
  await page.getByText('Welcome to Keyboard HUB').waitFor();
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.evaluate(async () => { await fetch('./3key_v104.bin'); await fetch('./update.json'); await fetch('./firmware-manifest.json'); });
  const cached = await page.evaluate(async () => {
    const urls = [];
    for (const k of await caches.keys()) for (const r of await (await caches.open(k)).keys()) urls.push(new URL(r.url).pathname);
    return urls;
  });
  assert.ok(cached.length > 10, 'shell is precached');
  for (const bad of ['.bin', 'update.json', 'firmware-manifest.json', 'sw.js']) {
    assert.equal(cached.filter((u) => u.endsWith(bad)).length, 0, `${bad} must not be cached`);
  }
  await page.reload(); // let the worker take control of the page
  await context.setOffline(true);
  await page.reload();
  await page.getByText('Welcome to Keyboard HUB').waitFor({ timeout: 10000 });
  await context.close();
});

await test('PWA: manifest is valid and every icon exists at its declared size', async () => {
  const m = await (await fetch(url + '/manifest.webmanifest')).json();
  assert.ok(m.name && m.short_name && m.start_url && m.display === 'standalone');
  assert.ok(m.icons.some((i) => i.purpose === 'maskable'), 'has a maskable icon');
  const sharp = await import('node:fs/promises');
  for (const icon of m.icons) {
    const buf = Buffer.from(await (await fetch(`${url}/${icon.src}`)).arrayBuffer());
    assert.equal(buf.readUInt32BE(16), Number(icon.sizes.split('x')[0]), `${icon.src} width`);
    assert.equal(buf.readUInt32BE(20), Number(icon.sizes.split('x')[1]), `${icon.src} height`);
  }
  void sharp;
});

await test('every page loads: index, docs, 404 (no errors, CSP clean)', async () => {
  for (const p of ['/index.html', '/doc.html', '/doc-en.html', '/404.html']) {
    const { context, page, problems } = await open();
    await page.goto(url + p);
    await page.waitForLoadState('networkidle');
    assert.deepEqual(await page.evaluate(() => window.__csp), [], `${p} CSP violations`);
    assert.deepEqual(problems.filter((x) => !/404/.test(x)), [], `${p} errors`);
    await context.close();
  }
});

await test('accessibility scan (axe) finds no critical or serious issues on the landing screen', async () => {
  // bypassCSP only so the test can inject the scanner; the shipped policy is unchanged.
  const { context, page } = await open({ bypassCSP: true });
  await page.goto(url + '/');
  await page.getByText('Welcome to Keyboard HUB').waitFor();
  await page.addScriptTag({ content: await readFile(require.resolve('axe-core/axe.min.js'), 'utf8') });
  const { violations } = await page.evaluate(() => axe.run(document, { resultTypes: ['violations'] }));
  for (const v of violations) console.log(`        axe ${v.impact}: ${v.id} (${v.nodes.length}) ${v.help}`);
  const serious = violations.filter((v) => v.impact === 'critical' || v.impact === 'serious');
  assert.deepEqual(serious.map((v) => v.id), [], 'critical/serious accessibility issues');
  const viewport = await page.evaluate(() => [...document.querySelectorAll('meta[name=viewport]')].map((m) => m.content).join(' '));
  assert.doesNotMatch(viewport, /maximum-scale|user-scalable=no/, 'zoom must not be restricted');
  await context.close();
});

await browser.close();
server.close();

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);
