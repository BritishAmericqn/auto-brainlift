const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Generate summary (manual trigger)
  generateSummary: (commitHash) => ipcRenderer.invoke('generate-summary', commitHash),
  
  // Analyze WIP (work in progress)
  analyzeWip: (mode) => ipcRenderer.invoke('analyze-wip', mode),
  
  // Get latest generated files
  getLatestFiles: () => ipcRenderer.invoke('get-latest-files'),
  
  // Listen for summary generation events
  onSummaryProgress: (callback) => {
    ipcRenderer.on('summary-progress', (event, data) => callback(data));
  },
  
  // Remove listener
  removeSummaryListener: () => {
    ipcRenderer.removeAllListeners('summary-progress');
  },
  
  // Project management API
  project: {
    create: (projectPath, name) => ipcRenderer.invoke('project:create', projectPath, name),
    switch: (projectId) => ipcRenderer.invoke('project:switch', projectId),
    remove: (projectId) => ipcRenderer.invoke('project:remove', projectId),
    getAll: () => ipcRenderer.invoke('project:get-all'),
    getCurrent: () => ipcRenderer.invoke('project:get-current'),
    updateSettings: (projectId, settings) => ipcRenderer.invoke('project:update-settings', projectId, settings),
    
    // Event listeners
    onListChanged: (callback) => {
      ipcRenderer.on('project:list-changed', callback);
    },
    onCurrentChanged: (callback) => {
      ipcRenderer.on('project:current-changed', (event, project) => callback(project));
    },
    onSettingsChanged: (callback) => {
      ipcRenderer.on('project:settings-changed', (event, project) => callback(project));
    },
    
    // Remove listeners
    removeListeners: () => {
      ipcRenderer.removeAllListeners('project:list-changed');
      ipcRenderer.removeAllListeners('project:current-changed');
      ipcRenderer.removeAllListeners('project:settings-changed');
    }
  },
  
  // Global settings API
  settings: {
    getGlobal: () => ipcRenderer.invoke('settings:get-global'),
    updateGlobal: (settings) => ipcRenderer.invoke('settings:update-global', settings),
    
    // Event listeners
    onGlobalChanged: (callback) => {
      ipcRenderer.on('settings:global-changed', (event, settings) => callback(settings));
    },
    
    // Remove listeners
    removeListeners: () => {
      ipcRenderer.removeAllListeners('settings:global-changed');
    }
  },
  
  // Dialog API
  dialog: {
    selectDirectory: () => ipcRenderer.invoke('dialog:select-directory')
  },
  
  // Cache API
  cache: {
    getStats: () => ipcRenderer.invoke('cache:get-stats'),
    clear: (cacheType) => ipcRenderer.invoke('cache:clear', cacheType)
  },
  
  // Budget API
  budget: {
    getUsage: () => ipcRenderer.invoke('budget:get-usage')
  },
  
  // Cost API
  cost: {
    preview: (diffText) => ipcRenderer.invoke('cost:preview', diffText)
  },
  
  // File API
  file: {
    getHistory: (fileType) => ipcRenderer.invoke('get-file-history', fileType),
    getContent: (filePath) => ipcRenderer.invoke('get-file-content', filePath)
  },

  // Git API
  git: {
    status: () => ipcRenderer.invoke('git:status'),
    add: (files) => ipcRenderer.invoke('git:add', files),
    reset: (files) => ipcRenderer.invoke('git:reset', files),
    generateCommitMessage: () => ipcRenderer.invoke('git:generate-commit-message'),
    commit: (message) => ipcRenderer.invoke('git:commit', message),
    push: () => ipcRenderer.invoke('git:push'),
    pull: () => ipcRenderer.invoke('git:pull')
  },

  // Style Guide API
  styleGuide: {
    upload: (filePath, options) => ipcRenderer.invoke('style-guide:upload', filePath, options),
    preview: () => ipcRenderer.invoke('style-guide:preview'),
    apply: () => ipcRenderer.invoke('style-guide:apply'),
    getStatus: () => ipcRenderer.invoke('style-guide:get-status')
  },

  // Slack API
  slack: {
    test: (token, channel) => ipcRenderer.invoke('slack:test', token, channel),
    sendSummary: (summaryData) => ipcRenderer.invoke('slack:send-summary', summaryData),
    testSummary: () => ipcRenderer.invoke('slack:test-summary'),
    sendProgressUpdate: () => ipcRenderer.invoke('slack:send-progress-update')
  }
}); 