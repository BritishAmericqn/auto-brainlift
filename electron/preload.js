const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Generate summary (manual trigger)
  generateSummary: (commitHash) => ipcRenderer.invoke('generate-summary', commitHash),
  
  // Get latest generated files
  getLatestFiles: () => ipcRenderer.invoke('get-latest-files'),
  
  // Listen for summary generation events
  onSummaryProgress: (callback) => {
    ipcRenderer.on('summary-progress', (event, data) => callback(data));
  },
  
  // Remove listener
  removeSummaryListener: () => {
    ipcRenderer.removeAllListeners('summary-progress');
  }
}); 