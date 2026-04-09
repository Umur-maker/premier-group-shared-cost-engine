const { app, BrowserWindow, protocol, net, ipcMain, dialog } = require("electron");
const path = require("path");
const { spawn, execSync } = require("child_process");
const http = require("http");
const { autoUpdater } = require("electron-updater");

let mainWindow = null;
let splashWindow = null;
let backendProcess = null;
const PORT = 8000;

// Determine paths based on packaged or dev mode
const isDev = !app.isPackaged;
const resourcesPath = isDev
  ? path.join(__dirname, "..")
  : process.resourcesPath;

const backendPath = isDev
  ? null // In dev mode, start backend manually
  : path.join(resourcesPath, "backend", "run_server.exe");

const frontendPath = isDev
  ? path.join(resourcesPath, "frontend", "out")
  : path.join(resourcesPath, "frontend");

const dataDir = path.join(app.getPath("userData"), "data");

function startBackend() {
  if (isDev) {
    console.log("[Electron] Dev mode — start backend manually: python -m uvicorn backend.main:app --port 8000");
    return;
  }

  const env = {
    ...process.env,
    PREMIER_DATA_DIR: dataDir,
    PREMIER_ELECTRON: "1",
    PREMIER_PORT: String(PORT),
  };

  console.log(`[Electron] Starting backend: ${backendPath}`);
  console.log(`[Electron] Data directory: ${dataDir}`);

  backendProcess = spawn(backendPath, [], {
    env,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });

  backendProcess.stdout.on("data", (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on("data", (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.on("error", (err) => {
    console.error("[Electron] Failed to start backend:", err.message);
  });

  backendProcess.on("exit", (code) => {
    console.log(`[Electron] Backend exited with code ${code}`);
    backendProcess = null;
  });
}

function waitForBackend(maxAttempts = 50) {
  return new Promise((resolve, reject) => {
    let attempts = 0;

    function check() {
      attempts++;
      const req = http.get(`http://127.0.0.1:${PORT}/api/health`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          retry();
        }
      });
      req.on("error", retry);
      req.setTimeout(500, () => {
        req.destroy();
        retry();
      });
    }

    function retry() {
      if (attempts >= maxAttempts) {
        reject(new Error("Backend did not start in time"));
      } else {
        setTimeout(check, 300);
      }
    }

    check();
  });
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 280,
    frame: false,
    transparent: false,
    resizable: false,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  splashWindow.loadFile(path.join(__dirname, "splash.html"));
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: "Premier Cost Engine",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Load frontend from static files via custom protocol
  mainWindow.loadURL("app://-/index.html");

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function killBackend() {
  if (backendProcess) {
    try {
      // Windows: kill the process tree
      execSync(`taskkill /pid ${backendProcess.pid} /T /F`, { stdio: "ignore" });
    } catch {
      // Process may already be dead
    }
    backendProcess = null;
  }
}

// ── AUTO-UPDATER ──

function setupAutoUpdater() {
  autoUpdater.autoDownload = false;
  autoUpdater.autoInstallOnAppQuit = true;

  autoUpdater.on("update-available", (info) => {
    console.log(`[Updater] Update available: v${info.version}`);
    if (!mainWindow) return;

    dialog.showMessageBox(mainWindow, {
      type: "info",
      title: "Update Available",
      message: `A new version (v${info.version}) is available.`,
      detail: "Would you like to download and install it now? Your data will not be affected.",
      buttons: ["Update Now", "Later"],
      defaultId: 0,
      cancelId: 1,
    }).then(({ response }) => {
      if (response === 0) {
        autoUpdater.downloadUpdate();
        dialog.showMessageBox(mainWindow, {
          type: "info",
          title: "Downloading Update",
          message: "The update is being downloaded in the background. You will be notified when it is ready.",
          buttons: ["OK"],
        });
      }
    });
  });

  autoUpdater.on("update-downloaded", () => {
    console.log("[Updater] Update downloaded, prompting restart");
    if (!mainWindow) return;

    dialog.showMessageBox(mainWindow, {
      type: "info",
      title: "Update Ready",
      message: "The update has been downloaded. The application will restart to apply the update.",
      buttons: ["Restart Now", "Later"],
      defaultId: 0,
      cancelId: 1,
    }).then(({ response }) => {
      if (response === 0) {
        killBackend();
        autoUpdater.quitAndInstall(true, true);
      }
    });
  });

  autoUpdater.on("error", (err) => {
    console.log("[Updater] Error:", err.message);
    // Silent — don't bother user with update errors
  });

  // Check for updates after a short delay
  setTimeout(() => {
    autoUpdater.checkForUpdates().catch(() => {});
  }, 5000);
}

// Register custom protocol for serving static frontend files
protocol.registerSchemesAsPrivileged([
  { scheme: "app", privileges: { standard: true, secure: true, supportFetchAPI: true } },
]);

app.on("ready", async () => {
  // Register app:// protocol handler
  protocol.handle("app", (request) => {
    let filePath = request.url.replace("app://-/", "");
    if (!filePath || filePath === "") filePath = "index.html";

    // Remove query strings and hash
    filePath = filePath.split("?")[0].split("#")[0];

    const fullPath = path.join(frontendPath, filePath);

    // Try the exact path first, then try with .html extension (for Next.js routes)
    return net.fetch(`file://${fullPath}`).catch(() => {
      return net.fetch(`file://${fullPath}.html`).catch(() => {
        // Fallback to index.html for client-side routing
        return net.fetch(`file://${path.join(frontendPath, "index.html")}`);
      });
    });
  });

  createSplashWindow();
  startBackend();

  try {
    if (isDev) {
      await waitForBackend(100);
    } else {
      await waitForBackend(50);
    }
  } catch (err) {
    console.error("[Electron]", err.message);
    if (!isDev) {
      dialog.showErrorBox(
        "Startup Error",
        "Backend failed to start. Port 8000 may already be in use.\n\nPlease close any other applications using port 8000 and try again."
      );
      app.quit();
      return;
    }
  }

  createMainWindow();

  if (splashWindow) {
    splashWindow.close();
    splashWindow = null;
  }

  // Auto-update (only in packaged mode)
  if (!isDev) {
    setupAutoUpdater();
  }
});

app.on("window-all-closed", () => {
  killBackend();
  app.quit();
});

app.on("before-quit", () => {
  killBackend();
});
