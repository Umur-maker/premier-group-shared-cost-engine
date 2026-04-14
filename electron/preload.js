const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  getDataDir: () => ipcRenderer.invoke("get-data-dir"),
  selectDataDir: () => ipcRenderer.invoke("select-data-dir"),
  setDataDir: (newPath) => ipcRenderer.invoke("set-data-dir", newPath),
});
