# MK1300 V2 Keyboard Software — web app

The MK1300 V2 configuration app as a website. It talks to the keyboard with
**WebHID**, so there is nothing to install. This project wraps the existing UI
(`../mk1300-mac/build`, an exported Next.js app) with a production build,
security headers, offline support and tests. The UI bundle itself is not modified.

## Run it

```bash
cd mk1300-web
npm install
npm start            # builds, then serves http://127.0.0.1:8080
```

Open it in **Chrome or Edge**, plug in the keyboard, click "Initialise device".
`localhost` counts as a secure origin, so WebHID works without HTTPS locally.

```bash
npm test             # build + 13 end-to-end tests (needs: npx playwright install chromium)
```

## What this adds on top of the UI

| Area | What it does |
|---|---|
| **Browser support gate** | Safari, Firefox, phones and non-HTTPS pages get a clear explanation instead of a dead button. The app behind it is made inert. |
| **Firmware integrity** | Every `.bin` the app downloads is checked against a SHA-256 manifest generated at build time before it can be flashed. Tampered, truncated, unlisted or mismatched files are rejected. |
| **Security headers** | Strict CSP (no `unsafe-inline`/`unsafe-eval` for scripts; inline scripts are pinned by hash), `Permissions-Policy: hid=(self)`, nosniff, frame denial, COOP/CORP, HSTS. |
| **Caching** | Hashed assets are immutable for a year. HTML, firmware, `update.json` and manifests are never cached, so a stale firmware file can't be served. |
| **Offline / installable** | Service worker precaches the app shell; installable as a PWA. Firmware and manifests always bypass the cache. A new version waits until all tabs close, so a session is never swapped mid-use. |
| **Accessibility** | Alt text for the keyboard image, viewport zoom un-blocked, and an accessible, keyboard-friendly support gate. |
| **Glass theme** | Light, frosted-glass look in soft blues, oranges and whites (`src/theme-glass.css`): layered panels with blur and transparency, wide low-opacity shadows, rounded corners, dark-navy text for contrast, orange accent button. Fluid on phone-width screens. Honours reduced-transparency, high-contrast and reduced-motion settings. All colours are tokens at the top of the file. |
| **Tests** | Headers, caching, CSP cleanliness on every page, the gate, firmware tamper cases, offline behaviour, PWA manifest and icons, and an axe accessibility scan. |

## Deploy

The site must be served over **HTTPS**. Any static host works; the build writes
the right header config for each:

| Host | How |
|---|---|
| **Vercel** | Import the repo, set Root Directory to `mk1300-web`. `vercel.json` (generated, committed) sets build command, output and headers. |
| **Netlify / Cloudflare Pages** | Build command `node scripts/build.mjs`, publish directory `dist`. Headers come from `dist/_headers`. |
| **GitHub Pages** | Works, but **cannot set response headers**, so CSP, HSTS and `Permissions-Policy` would be missing. Not recommended. |

The build reads the UI from `../mk1300-mac/build`. If you only deploy this
folder, set `MK_UI_SOURCE` to the exported UI's location.

## Known gaps (need the original Next.js source)

- **Theme coverage.** The glass theme was checked on the landing screen, the docs
  pages and the browser-support screen. The configuration screens (lighting, key
  mapping, macros) only appear once a keyboard is connected, so they were
  **not seen**. The theme restyles them through the app's shared colour classes
  and Chakra components and should carry over, but expect some tuning there.
  `src/theme-glass.css` is the one file to adjust.
- **Layout is not truly mobile-first.** The landing page stacks cleanly on a phone,
  but WebHID doesn't exist in mobile browsers, so the keyboard can't be configured
  from one. The responsive work is for viewing and for narrow desktop windows.
- Remaining accessibility findings (moderate): no `<main>` landmark, no `<h1>`
  (the title is a `<span>`), content outside landmarks. `src/a11y-patch.js`
  fixes what can be fixed safely from outside; delete it once the source is fixed.
- `style-src` still allows `'unsafe-inline'` because the UI library (Chakra/Emotion) injects styles at runtime.
- **`update.json` lists six devices whose firmware files are not in the bundle**
  (`36ae_fe9c`, `feae`, `fea3`, `fda1`, `fead`, `fe9d`). A firmware update for
  those would 404. The build prints a warning; use `node scripts/build.mjs --strict` to fail on it.
- The device this app targets (`36ae:fe12`) has **no entry in `update.json`**.
  Check how its firmware update is meant to work before relying on that feature.
- The UI links to third-party downloads on GitHub
  (`github.com/daddasdsa/sd_tools/releases/...`, "SDTech Options"). Confirm those are
  yours or remove them.
- Firmware verification protects against corruption and bad deploys, not against
  someone who controls your web server (they could replace the firmware and the manifest).
- The layout is built for a ~1800px-wide desktop window. There is no responsive
  layout; use browser zoom on small screens.
- Not tested with a real keyboard. Tests use a stubbed WebHID. Try connect,
  lighting, macros and a firmware update on a spare device first.
