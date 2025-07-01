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
          // Pass project path as environment variable instead
          PROJECT_PATH: currentProject.path,
          PROJECT_NAME: currentProject.name
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