const { app, BrowserWindow, Menu, globalShortcut, screen, shell } = require('electron');
const fs = require('fs');
const path = require('path');
const { getPermission } = require('./utils/comm');

const isDevelopment = process.env.NODE_ENV === 'development';
const isMac = process.platform === 'darwin';
const isWindows = process.platform === 'win32';
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';

// Windows installer shortcut handling only; meaningless (and unavailable) elsewhere.
if (isWindows && require('electron-squirrel-startup')) {
  app.quit();
}

// The UI is laid out for an 1800x1000 viewport. Small laptop screens (a 13"
// MacBook Air is 1440x900 points) cannot fit that, so scale the page down
// instead of letting it overflow.
const DESIGN_WIDTH = 1800;
const DESIGN_HEIGHT = 1000;
const MIN_ZOOM = 0.6;

const fitZoom = (win) => {
  const [width, height] = win.getContentSize();
  const zoom = Math.min(1, width / DESIGN_WIDTH, height / DESIGN_HEIGHT);
  return Math.max(MIN_ZOOM, zoom);
};

const buildMenu = () => {
  const template = [
    ...(isMac
      ? [
          {
            label: app.name,
            submenu: [
              { role: 'about' },
              { type: 'separator' },
              { role: 'hide' },
              { role: 'hideOthers' },
              { role: 'unhide' },
              { type: 'separator' },
              { role: 'quit' },
            ],
          },
        ]
      : []),
    { role: 'editMenu' },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'togglefullscreen' },
        ...(isDevelopment ? [{ role: 'toggleDevTools' }] : []),
      ],
    },
    { role: 'windowMenu' },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
};

const createWindow = () => {
  const { width: areaW, height: areaH } = screen.getPrimaryDisplay().workAreaSize;

  const mainWindow = new BrowserWindow({
    width: Math.min(DESIGN_WIDTH, areaW),
    height: Math.min(DESIGN_HEIGHT, areaH),
    minWidth: Math.min(DESIGN_WIDTH * MIN_ZOOM, areaW),
    minHeight: Math.min(DESIGN_HEIGHT * MIN_ZOOM, areaH),
    title: 'MK1300 V2 Keyboard Software',
    backgroundColor: '#000000', // matches the dark UI, avoids a white flash on launch
    autoHideMenuBar: true, // Windows/Linux only; macOS always shows the system menu bar
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js'),
      zoomFactor: 1.0,
    },
    // macOS takes its icon from the app bundle; this is only for Windows/Linux.
    ...(isMac ? {} : { icon: path.resolve(__dirname, './assets/icon.ico') }),
  });

  const applyZoom = () => {
    if (mainWindow.isDestroyed()) return;
    mainWindow.webContents.setZoomFactor(fitZoom(mainWindow));
  };

  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.setVisualZoomLevelLimits(1, 1); // disable pinch zoom
    applyZoom();
    try {
      mainWindow.webContents.insertCSS(fs.readFileSync(path.join(__dirname, 'assets/mac.css'), 'utf8'));
    } catch (e) {
      console.warn('mac.css not loaded:', e.message);
    }
  });
  mainWindow.on('resize', applyZoom);
  mainWindow.on('enter-full-screen', applyZoom);
  mainWindow.on('leave-full-screen', applyZoom);

  // Registered once per session. (The original registered these inside the
  // select-hid-device handler, stacking duplicates on every device prompt.)
  const hidSession = mainWindow.webContents.session;
  hidSession.on('hid-device-added', (event, device) => {
    console.log('hid-device-added', device);
  });
  hidSession.on('hid-device-removed', (event, device) => {
    console.log('hid-device-removed', device);
  });

  hidSession.on('select-hid-device', (event, details, callback) => {
    event.preventDefault();
    const match = (details.deviceList || []).find((device) =>
      getPermission(device.vendorId, device.productId)
    );
    // Passing no id cancels the request instead of leaving the page's
    // requestDevice() promise pending forever when no supported keyboard is attached.
    if (match) {
      callback(match.deviceId);
    } else {
      callback();
    }
  });

  hidSession.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
    return Boolean(
      details &&
        details.device &&
        permission === 'hid' &&
        getPermission(details.device.vendorId, details.device.productId)
    );
  });

  hidSession.setDevicePermissionHandler((details) => {
    return Boolean(
      details &&
        details.device &&
        details.deviceType === 'hid' &&
        getPermission(details.device.vendorId, details.device.productId)
    );
  });

  if (isDevelopment) {
    globalShortcut.register('CommandOrControl+\\', () => {
      mainWindow.webContents.openDevTools();
    });
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }
};

app.commandLine.appendSwitch('disable-hid-blocklist');

app.setName('MK1300 V2 Keyboard Software');

app.whenReady().then(() => {
  buildMenu();
  createWindow();

  // On macOS, re-create a window when the dock icon is clicked and none are open.
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS where apps stay active
// until the user quits explicitly with Cmd+Q.
app.on('window-all-closed', () => {
  if (!isMac) {
    app.quit();
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('web-contents-created', (e, webContents) => {
  // Open links in the user's browser, never in a new Electron window.
  webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });
});
