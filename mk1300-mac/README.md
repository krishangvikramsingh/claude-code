# MK1300 V2 Keyboard Software — macOS port

Mac build of the Ant Esports MK1300 V2 keyboard configuration app (v1.0.0).

The Windows app is an Electron 30.5.1 shell around a Next.js UI that talks to
the keyboard over **WebHID** (`navigator.hid`, vendor `0x36ae`, product
`0xfe12`). That path works the same on macOS, so the UI bundle in `build/` and
the firmware `.bin` files are unchanged. Only the Electron shell changed.

## Build on a Mac

Requires macOS, Node 18+ and Xcode command line tools.

```bash
cd mk1300-mac
npm install
npm start              # run from source
npm run dist:mac       # produces dist/*.dmg for arm64 and x64
```

## What changed from the Windows app

| Area | Change |
|---|---|
| `main/index.js` | `electron-squirrel-startup` only on Windows; macOS app menu (Cmd+Q, copy/paste, window); app stays alive after the last window closes; links open in the default browser and are never opened as new windows. |
| Window size | Was a fixed 1800x1000 minimum, larger than a 13" MacBook screen. The window now fits the screen and the page scales (zoom 0.6–1.0) so the layout never overflows. |
| HID handler | Listeners were registered inside the device-picker callback, stacking duplicates on every prompt, and the picker never resolved when no supported keyboard was attached. Both fixed. |
| `main/assets/mac.css` | Font smoothing, `prefers-reduced-motion` support, visible keyboard focus. Additive; the original bundle is untouched. |
| Packaging | `electron-builder` DMG config, hardened-runtime entitlements, 1024px app icon. |
| Removed | Windows `.ico` window icon on macOS, NSIS installer, `elevate.exe`. |

## Before you ship

- **Not tested against a real keyboard.** It was built and smoke-tested on
  Linux with the real Electron 30.5.1 (boots, menu, scaling, CSS injection,
  WebHID present). Plug in an MK1300 V2 on a Mac and check connect, lighting,
  key mapping, macros and a firmware update.
- **Input Monitoring.** macOS may ask for permission the first time the app
  opens the keyboard (System Settings > Privacy & Security > Input Monitoring).
  If connecting fails silently, check there first.
- **Signing.** Unsigned builds trigger a Gatekeeper warning. For distribution,
  set `CSC_LINK`/`CSC_KEY_PASSWORD` and Apple notarization variables for
  `electron-builder`.
- **Firmware updates are the riskiest feature.** Test on a spare keyboard
  first.
- **Key labels.** The device UI labels the Windows key "Win" because that is
  the HID key it sends. On a Mac it acts as Command. The labels live in the
  minified bundle and were left alone; change them in the original Next.js
  source if you want "Cmd"/"Opt" shown.
- **App icon** is the 256px wordmark upscaled on a dark tile. Swap in a vector
  or 1024px version of the logo for a crisper icon at `assets-mac/icon.png`.
