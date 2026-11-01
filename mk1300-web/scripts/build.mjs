#!/usr/bin/env node
/* Builds the deployable web app into dist/.
 *
 *   node scripts/build.mjs [--strict]
 *
 * Input:  the exported Next.js UI (default ../mk1300-mac/build, override with
 *         MK_UI_SOURCE=/path/to/export).
 * Output: dist/ (static site), vercel.json (committed so Vercel can read it) and
 *         .build/headers.json (used by the local server and the tests).
 *
 * The original UI bundle is copied as-is. Everything added is additive: head
 * tags, the support gate, the firmware guard, the service worker, the manifest,
 * a firmware checksum manifest, and security headers with CSP script hashes.
 */
import { createHash } from 'node:crypto';
import { cp, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC_UI = path.resolve(ROOT, process.env.MK_UI_SOURCE || '../mk1300-mac/build');
const DIST = path.join(ROOT, 'dist');
const STRICT = process.argv.includes('--strict');

const SITE = {
  name: 'MK1300 V2 Keyboard Software',
  description:
    'Configure lighting, key mappings and macros on your Ant Esports MK1300 V2 keyboard, and update its firmware, right from the browser.',
  themeColor: '#eaf3ff',
};

const sha256 = (buf) => createHash('sha256').update(buf).digest();
const hex = (buf) => sha256(buf).toString('hex');
const b64 = (buf) => sha256(buf).toString('base64');

async function walk(dir, base = dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(full, base)));
    else out.push(path.relative(base, full).split(path.sep).join('/'));
  }
  return out.sort();
}

const warnings = [];
const warn = (m) => {
  warnings.push(m);
  console.warn('  warning:', m);
};

async function main() {
  try {
    await stat(path.join(SRC_UI, 'index.html'));
  } catch {
    throw new Error(`UI export not found at ${SRC_UI} (no index.html). Set MK_UI_SOURCE.`);
  }

  console.log('Building from', path.relative(ROOT, SRC_UI) || SRC_UI);
  await rm(DIST, { recursive: true, force: true });
  await cp(SRC_UI, DIST, { recursive: true });

  // Static files added by this project.
  for (const f of ['support-gate.js', 'support-gate.css', 'firmware-guard.js', 'pwa.js', 'a11y-patch.js', 'theme-glass.css', 'manifest.webmanifest', 'robots.txt']) {
    await cp(path.join(ROOT, 'src', f), path.join(DIST, f));
  }
  await cp(path.join(ROOT, 'src/icons'), path.join(DIST, 'icons'), { recursive: true });

  // ---- Firmware checksum manifest --------------------------------------
  const files = await walk(DIST);
  const firmware = {};
  for (const f of files.filter((f) => /^[^/]+\.bin$/i.test(f))) {
    const buf = await readFile(path.join(DIST, f));
    firmware[f] = { sha256: hex(buf), size: buf.length };
  }
  await writeFile(
    path.join(DIST, 'firmware-manifest.json'),
    JSON.stringify({ schema: 1, algorithm: 'sha256', files: firmware }, null, 2) + '\n'
  );

  // Every firmware file update.json points at has to exist, or "update" would 404.
  const updates = JSON.parse(await readFile(path.join(DIST, 'update.json'), 'utf8'));
  for (const [device, info] of Object.entries(updates)) {
    if (!info || !info.file || !firmware[info.file]) {
      warn(`update.json lists ${device} -> ${info && info.file}, but no such firmware file ships`);
    }
  }
  const referenced = new Set(Object.values(updates).map((u) => u && u.file));
  const unreferenced = Object.keys(firmware).filter((f) => !referenced.has(f));
  console.log(`  firmware: ${Object.keys(firmware).length} files hashed (${unreferenced.length} are not listed in update.json; kept because the UI may reference them directly)`);

  // ---- HTML: head tags, gate, guard ------------------------------------
  const inlineHashes = new Set();
  const htmlFiles = files.filter((f) => /^[^/]+\.html$/.test(f));
  for (const f of htmlFiles) {
    let html = await readFile(path.join(DIST, f), 'utf8');

    // The UI caps zoom at 0.6, which blocks users from zooming in (WCAG 1.4.4).
    html = html.replace(/,\s*maximum-scale=[0-9.]+/g, '').replace(/,\s*user-scalable=no/g, '');

    if (!/<html[^>]*\blang=/.test(html)) html = html.replace(/<html(\s|>)/, '<html lang="en"$1');

    // Lets the theme scope rules to a page type without touching the UI bundle.
    const pageType = f === 'index.html' ? 'app' : /^doc/.test(f) ? 'docs' : 'other';
    html = html.replace('<html ', `<html data-page="${pageType}" `);

    const headStart =
      '<link rel="stylesheet" href="./support-gate.css"/>' +
      '<script src="./support-gate.js"></script>' +
      '<script src="./firmware-guard.js"></script>';
    const meta = [
      !/<title>/.test(html) && `<title>${SITE.name}</title>`,
      !/name="description"/.test(html) && `<meta name="description" content="${SITE.description}"/>`,
      `<meta name="theme-color" content="${SITE.themeColor}"/>`,
      '<meta name="color-scheme" content="light"/>',
      '<meta name="application-name" content="MK1300 V2"/>',
      `<meta property="og:title" content="${SITE.name}"/>`,
      `<meta property="og:description" content="${SITE.description}"/>`,
      '<meta property="og:type" content="website"/>',
      '<link rel="manifest" href="./manifest.webmanifest"/>',
      !/rel="icon"/.test(html) && '<link rel="icon" href="./favicon.ico"/>',
      '<link rel="apple-touch-icon" href="./icons/apple-touch-icon.png"/>',
      '<link rel="stylesheet" href="./theme-glass.css"/>',
      '<script src="./pwa.js" defer></script>',
      '<script src="./a11y-patch.js" defer></script>',
    ]
      .filter(Boolean)
      .join('');

    if (!html.includes('<head>')) throw new Error(`${f}: no <head> to inject into`);
    html = html.replace('<head>', `<head>${headStart}`).replace('</head>', `${meta}</head>`);
    html = html.replace(
      /(<body[^>]*>)/,
      '$1<noscript><div class="mk-noscript"><p>This app needs JavaScript to configure your keyboard. Please enable it and reload.</p></div></noscript>'
    );

    for (const m of html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)) {
      if (m[1].trim()) inlineHashes.add(`'sha256-${b64(Buffer.from(m[1], 'utf8'))}'`);
    }
    await writeFile(path.join(DIST, f), html);
  }

  // ---- Build id + service worker ---------------------------------------
  const all = (await walk(DIST)).filter((f) => f !== 'sw.js');
  const idHash = createHash('sha256');
  for (const f of all) idHash.update(f).update(await readFile(path.join(DIST, f)));
  const buildId = idHash.digest('hex').slice(0, 12);

  const precache = [
    './',
    ...all.filter((f) => /^[^/]+\.html$/.test(f)),
    ...all.filter((f) => f.startsWith('_next/static/')),
    'manifest.webmanifest',
    'support-gate.js',
    'support-gate.css',
    'firmware-guard.js',
    'pwa.js',
    'a11y-patch.js',
    'theme-glass.css',
    'favicon.ico',
    'home_device.png',
    ...all.filter((f) => f.startsWith('icons/')),
  ]
    .filter((f) => all.includes(f) || f === './')
    .map((f) => (f === './' ? f : './' + f));

  const swSrc = await readFile(path.join(ROOT, 'src/sw.js'), 'utf8');
  if (!swSrc.includes("'__BUILD_ID__'") || !swSrc.includes('= __PRECACHE__;')) {
    throw new Error('src/sw.js is missing its build placeholders');
  }
  // Function replacers: a plain string would treat "$" in the data as a pattern.
  const swOut = swSrc
    .replace("'__BUILD_ID__'", () => JSON.stringify(buildId))
    .replace('= __PRECACHE__;', () => '= ' + JSON.stringify([...new Set(precache)], null, 2) + ';');
  if (swOut.includes('__BUILD_ID__') || swOut.includes('__PRECACHE__')) throw new Error('sw.js placeholders left unreplaced');
  await writeFile(path.join(DIST, 'sw.js'), swOut);
  await writeFile(path.join(DIST, 'version.json'), JSON.stringify({ build: buildId }) + '\n');

  // ---- Security headers ------------------------------------------------
  const csp = [
    "default-src 'self'",
    `script-src 'self' ${[...inlineHashes].sort().join(' ')}`.trim(),
    "style-src 'self' 'unsafe-inline'", // the UI library (Chakra/Emotion) injects style tags at runtime
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self'",
    "worker-src 'self'",
    "manifest-src 'self'",
    "media-src 'self' blob:",
    "object-src 'none'",
    "frame-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join('; ');

  const noCache = 'no-cache, must-revalidate';
  const security = {
    'Content-Security-Policy': csp,
    // WebHID is allowed for this origin only; everything else sensitive is off.
    'Permissions-Policy': 'hid=(self), usb=(self), camera=(), microphone=(), geolocation=(), payment=(), serial=()',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
    'X-Frame-Options': 'DENY',
  };
  const hsts = { 'Strict-Transport-Security': 'max-age=63072000; includeSubDomains' };

  // Security headers apply everywhere. Cache-Control rules below never overlap
  // each other, so the result is the same on every host regardless of how it
  // merges rules that match the same path.
  const rules = [
    { source: '/(.*)', headers: security },
    { source: '/_next/static/(.*)', headers: { 'Cache-Control': 'public, max-age=31536000, immutable' } },
    { source: '/', headers: { 'Cache-Control': noCache } },
    { source: '/(.*)\\.html', headers: { 'Cache-Control': noCache } },
    { source: '/(.*)\\.bin', headers: { 'Cache-Control': noCache } },
    { source: '/update.json', headers: { 'Cache-Control': noCache } },
    { source: '/firmware-manifest.json', headers: { 'Cache-Control': noCache } },
    { source: '/version.json', headers: { 'Cache-Control': noCache } },
    { source: '/sw.js', headers: { 'Cache-Control': noCache, 'Service-Worker-Allowed': '/' } },
  ];

  await mkdir(path.join(ROOT, '.build'), { recursive: true });
  await writeFile(path.join(ROOT, '.build/headers.json'), JSON.stringify({ rules }, null, 2) + '\n');

  // Netlify / Cloudflare Pages
  const netlify = rules
    .map((r) => `${r.source.replace('/(.*)\\.html', '/*.html').replace('/(.*)\\.bin', '/*.bin').replace('/(.*)', '/*')}\n` +
      Object.entries({ ...r.headers, ...(r.source === '/(.*)' ? hsts : {}) }).map(([k, v]) => `  ${k}: ${v}`).join('\n'))
    .join('\n\n') + '\n';
  await writeFile(path.join(DIST, '_headers'), netlify);

  // Vercel (committed at the project root)
  const vercel = {
    $schema: 'https://openapi.vercel.sh/vercel.json',
    buildCommand: 'node scripts/build.mjs',
    outputDirectory: 'dist',
    cleanUrls: false,
    headers: rules.map((r) => ({
      source: r.source,
      headers: Object.entries({ ...r.headers, ...(r.source === '/(.*)' ? hsts : {}) }).map(([key, value]) => ({ key, value })),
    })),
  };
  await writeFile(path.join(ROOT, 'vercel.json'), JSON.stringify(vercel, null, 2) + '\n');

  console.log(`  build id ${buildId}; ${inlineHashes.size} inline scripts hashed for CSP; ${htmlFiles.length} HTML pages processed`);
  if (STRICT && warnings.length) {
    console.error(`\n${warnings.length} warning(s) with --strict`);
    process.exit(1);
  }
  console.log('Done. Output in dist/');
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
