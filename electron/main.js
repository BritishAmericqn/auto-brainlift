const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const { dialog } = require('electron');
const ProjectManager = require('./projectManager');

// Keep a global reference of the window object
let mainWindow;
let projectManager;

// Initialize project manager
async function initializeProjectManager() {
  projectManager = new ProjectManager();
  
  // Wait for settings to be initialized
  await projectManager.initializeSettings();
  await projectManager.loadFromSettings();
  
  // Check if we have a current project, if not, use the app directory as default
  const currentProject = projectManager.getCurrentProject();
  if (!currentProject) {
    // Create a default project for the current app directory
    const appPath = path.join(__dirname, '..');
    await projectManager.createProject(appPath, 'Auto-Brainlift Default');
  }
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/icon.png'), // We'll create this later
    titleBarStyle: 'default',
    backgroundColor: '#ffffff'
  });

  // Load the index.html file
  mainWindow.loadFile(path.join(__dirname, '../index.html'));

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  // Emitted when the window is closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// This method will be called when Electron has finished initialization
app.whenReady().then(async () => {
  // Initialize project manager first
  await initializeProjectManager();
  
  // Then create window
  createWindow();
  
  app.on('activate', function () {
    if (mainWindow === null) {
      createWindow();
    }
  });
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for communication with renderer process
ipcMain.handle('generate-summary', async (event, commitHash) => {
  try {
    // Get current project
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return {
        success: false,
        error: 'No project selected'
      };
    }
    
    // Log the action
    logToFile(`Manual summary generation triggered for project: ${currentProject.name}${commitHash ? ` for commit: ${commitHash}` : ''}`);
    projectManager.logToProject(currentProject.id, `Manual summary generation triggered${commitHash ? ` for commit: ${commitHash}` : ''}`);
    
    return new Promise((resolve, reject) => {
      // Spawn Python process
      const pythonPath = path.join(__dirname, '../venv/bin/python');
      const scriptPath = path.join(__dirname, '../agents/langgraph_agent.py');
      
      // Check if virtual environment exists, fallback to python3 if not
      const pythonCommand = fs.existsSync(pythonPath) ? pythonPath : 'python3';
      
      const args = [scriptPath];
      // Pass commit hash as a simple argument if provided
      if (commitHash) {
        args.push(commitHash);
      }
      
      logToFile(`Spawning Python process: ${pythonCommand} ${args.join(' ')}`);
      
      const pythonProcess = spawn(pythonCommand, args, {
        cwd: currentProject.path, // Run from project directory
        env: { 
          ...process.env,
          // Pass project context
          PROJECT_PATH: currentProject.path,
          PROJECT_NAME: currentProject.name,
          PROJECT_ID: currentProject.id,
          // Pass budget settings
          BUDGET_ENABLED: currentProject.settings.budgetEnabled ? 'true' : 'false',
          COMMIT_TOKEN_LIMIT: String(currentProject.settings.commitTokenLimit || 10000)
        }
      });
      
      let output = '';
      let errorOutput = '';
      
      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
        logToFile(`Python stdout: ${data.toString().trim()}`);
      });
      
      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
        logToFile(`Python stderr: ${data.toString().trim()}`);
      });
      
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          // Send progress update
          mainWindow.webContents.send('summary-progress', {
            status: 'complete',
            message: 'Summary generation completed'
          });
          
          resolve({
            success: true,
            message: 'Summary generation completed',
            timestamp: new Date().toISOString()
          });
        } else {
          const error = errorOutput || 'Unknown error occurred';
          logToFile(`Python process exited with code ${code}: ${error}`);
          
          // Send error update
          mainWindow.webContents.send('summary-progress', {
            status: 'error',
            message: error
          });
          
          resolve({
            success: false,
            error: error
          });
        }
      });
      
      pythonProcess.on('error', (err) => {
        logToFile(`Failed to start Python process: ${err.message}`);
        resolve({
          success: false,
          error: `Failed to start Python process: ${err.message}`
        });
      });
    });
  } catch (error) {
    logToFile(`Error in generate-summary: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-latest-files', async () => {
  try {
    // Get current project
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return {
        brainlift: null,
        context: null,
        error: 'No project selected'
      };
    }
    
    // Get project-specific paths
    const paths = projectManager.getProjectOutputPaths(currentProject.id);
    if (!paths) {
      return {
        brainlift: null,
        context: null,
        error: 'Invalid project paths'
      };
    }
    
    // Get latest files from project directories
    const latestBrainlift = await getLatestFile(paths.brainlifts);
    const latestContext = await getLatestFile(paths.contextLogs);
    
    return {
      brainlift: latestBrainlift,
      context: latestContext,
      projectName: currentProject.name
    };
  } catch (error) {
    logToFile(`Error getting latest files: ${error.message}`);
    return {
      brainlift: null,
      context: null,
      error: error.message
    };
  }
});

// Project management IPC handlers
ipcMain.handle('project:create', async (event, projectPath, name) => {
  try {
    const result = await projectManager.createProject(projectPath, name);
    if (result.success) {
      // Notify renderer of project list change
      mainWindow.webContents.send('project:list-changed');
    }
    return result;
  } catch (error) {
    logToFile(`Error creating project: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('project:switch', async (event, projectId) => {
  try {
    const result = await projectManager.switchProject(projectId);
    if (result.success) {
      // Notify renderer of current project change
      mainWindow.webContents.send('project:current-changed', result.project);
    }
    return result;
  } catch (error) {
    logToFile(`Error switching project: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('project:remove', async (event, projectId) => {
  try {
    const result = await projectManager.removeProject(projectId);
    if (result.success) {
      // Notify renderer of project list change
      mainWindow.webContents.send('project:list-changed');
    }
    return result;
  } catch (error) {
    logToFile(`Error removing project: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('project:get-all', async () => {
  try {
    return {
      success: true,
      projects: projectManager.getAllProjects()
    };
  } catch (error) {
    logToFile(`Error getting projects: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('project:get-current', async () => {
  try {
    return {
      success: true,
      project: projectManager.getCurrentProject()
    };
  } catch (error) {
    logToFile(`Error getting current project: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('project:update-settings', async (event, projectId, settings) => {
  try {
    const result = await projectManager.updateProjectSettings(projectId, settings);
    if (result.success) {
      // Notify renderer of settings change
      mainWindow.webContents.send('project:settings-changed', result.project);
    }
    return result;
  } catch (error) {
    logToFile(`Error updating project settings: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('settings:get-global', async () => {
  try {
    const settings = await projectManager.getGlobalSettings();
    return {
      success: true,
      settings: settings
    };
  } catch (error) {
    logToFile(`Error getting global settings: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('settings:update-global', async (event, settings) => {
  try {
    const result = await projectManager.updateGlobalSettings(settings);
    if (result.success) {
      // Notify renderer of settings change
      mainWindow.webContents.send('settings:global-changed', result.settings);
    }
    return result;
  } catch (error) {
    logToFile(`Error updating global settings: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

// Dialog handlers
ipcMain.handle('dialog:select-directory', async () => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
      title: 'Select Project Directory',
      buttonLabel: 'Select Folder'
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
      return {
        success: true,
        path: result.filePaths[0]
      };
    }
    
    return {
      success: false,
      canceled: true
    };
  } catch (error) {
    logToFile(`Error showing directory dialog: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

// Helper function to get the latest file from a directory
async function getLatestFile(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      return null;
    }
    
    const files = fs.readdirSync(dirPath)
      .filter(file => file.endsWith('.md'))
      .map(file => ({
        name: file,
        path: path.join(dirPath, file),
        time: fs.statSync(path.join(dirPath, file)).mtime.getTime()
      }))
      .sort((a, b) => b.time - a.time);
    
    if (files.length > 0) {
      const content = fs.readFileSync(files[0].path, 'utf8');
      return {
        name: files[0].name,
        content: content,
        timestamp: new Date(files[0].time).toISOString()
      };
    }
    
    return null;
  } catch (error) {
    logToFile(`Error reading directory ${dirPath}: ${error.message}`);
    return null;
  }
}

// Simple logging function
function logToFile(message) {
  const logDir = path.join(__dirname, '../logs');
  const logFile = path.join(logDir, 'electron.log');
  
  // Ensure log directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  
  // Append to log file
  fs.appendFileSync(logFile, logMessage);
  
  // Also log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.log(logMessage.trim());
  }
}

// Cache management IPC handlers
ipcMain.handle('cache:get-stats', async () => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return {
        success: false,
        error: 'No project selected'
      };
    }
    
    logToFile(`Getting cache stats for project: ${currentProject.id} (${currentProject.name})`);
    
    // Read real stats from the cache stats file
    const statsFile = path.join(
      app.getPath('userData'),
      'projects',
      currentProject.id,
      'cache',
      'stats.json'
    );
    
    logToFile(`Looking for stats file at: ${statsFile}`);
    
    if (fs.existsSync(statsFile)) {
      try {
        const statsData = JSON.parse(fs.readFileSync(statsFile, 'utf8'));
        logToFile(`Found cache stats: ${JSON.stringify(statsData.overall)}`);
        return {
          success: true,
          stats: statsData
        };
      } catch (error) {
        logToFile(`Error reading cache stats file: ${error.message}`);
        // Return default stats if file is corrupted
        return {
          success: true,
          stats: {
            overall: {
              hit_rate: 0,
              total_requests: 0,
              avg_latency_ms: 0
            }
          }
        };
      }
    }
    
    logToFile('Stats file does not exist yet');
    // Return empty stats if file doesn't exist yet
    return {
      success: true,
      stats: {
        overall: {
          hit_rate: 0,
          total_requests: 0,
          avg_latency_ms: 0
        },
        exact_cache: {
          hits: 0,
          misses: 0,
          sets: 0,
          evictions: 0,
          hit_rate: 0
        },
        semantic_cache: {
          hits: 0,
          misses: 0,
          sets: 0,
          evictions: 0,
          hit_rate: 0,
          entry_count: 0,
          total_bytes: 0
        },
        embeddings: {
          generations: 0,
          estimated_cost: 0
        }
      }
    };
  } catch (error) {
    logToFile(`Error getting cache stats: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('cache:clear', async (event, cacheType = 'all') => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return {
        success: false,
        error: 'No project selected'
      };
    }
    
    // Clear cache files for the project
    const cacheDir = path.join(
      app.getPath('userData'),
      'projects',
      currentProject.id,
      'cache'
    );
    
    if (fs.existsSync(cacheDir)) {
      if (cacheType === 'all' || cacheType === 'exact') {
        const exactCachePath = path.join(cacheDir, 'exact_cache.json');
        if (fs.existsSync(exactCachePath)) {
          fs.unlinkSync(exactCachePath);
        }
      }
      
      if (cacheType === 'all' || cacheType === 'semantic') {
        const semanticCachePath = path.join(cacheDir, 'semantic_cache.db');
        if (fs.existsSync(semanticCachePath)) {
          fs.unlinkSync(semanticCachePath);
        }
      }
    }
    
    // Also clear the stats file when clearing cache
    const statsFile = path.join(cacheDir, 'stats.json');
    if (fs.existsSync(statsFile)) {
      fs.unlinkSync(statsFile);
    }
    
    logToFile(`Cleared ${cacheType} cache for project ${currentProject.name}`);
    
    return {
      success: true,
      message: `${cacheType} cache cleared successfully`
    };
  } catch (error) {
    logToFile(`Error clearing cache: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

// Budget management IPC handlers
ipcMain.handle('budget:get-usage', async () => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return {
        success: false,
        error: 'No project selected'
      };
    }
    
    // Read usage data from project budget file
    const usageFile = path.join(
      app.getPath('userData'),
      'projects',
      currentProject.id,
      'budget',
      'usage.json'
    );
    
    if (fs.existsSync(usageFile)) {
      const usageData = JSON.parse(fs.readFileSync(usageFile, 'utf8'));
      
      // Calculate summaries
      const today = new Date().toISOString().split('T')[0];
      const todayUsage = usageData.daily_usage[today] || { tokens: 0, cost: 0 };
      
      return {
        success: true,
        usage: {
          today: todayUsage,
          total: {
            tokens: usageData.total_tokens,
            cost: usageData.total_cost
          },
          recent_commits: Object.entries(usageData.commits).slice(-5)
        }
      };
    }
    
    // Return empty usage if file doesn't exist
    return {
      success: true,
      usage: {
        today: { tokens: 0, cost: 0 },
        total: { tokens: 0, cost: 0 },
        recent_commits: []
      }
    };
  } catch (error) {
    logToFile(`Error getting budget usage: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('cost:preview', async (event, diffText) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return {
        success: false,
        error: 'No project selected'
      };
    }
    
    // Simple token estimation (4 chars per token for text, 3 for code)
    const looksLikeCode = diffText.includes('function') || 
                         diffText.includes('class') || 
                         diffText.includes('{') ||
                         diffText.includes('=>');
    
    const estimatedTokens = Math.ceil(diffText.length / (looksLikeCode ? 3 : 4));
    const costPerToken = 0.01 / 1000; // GPT-4-turbo pricing
    const estimatedCost = estimatedTokens * costPerToken;
    
    return {
      success: true,
      preview: {
        estimated_tokens: estimatedTokens,
        estimated_cost: estimatedCost,
        within_budget: estimatedTokens <= (currentProject.settings.commitTokenLimit || 10000),
        budget_enabled: currentProject.settings.budgetEnabled || false
      }
    };
  } catch (error) {
    logToFile(`Error previewing cost: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}); 