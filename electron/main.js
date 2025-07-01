const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Keep a global reference of the window object
let mainWindow;

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
app.whenReady().then(createWindow);

// Quit when all windows are closed
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC handlers for communication with renderer process
ipcMain.handle('generate-summary', async (event, commitHash) => {
  try {
    // Log the action
    logToFile(`Manual summary generation triggered${commitHash ? ` for commit: ${commitHash}` : ''}`);
    
    return new Promise((resolve, reject) => {
      // Spawn Python process
      const pythonPath = path.join(__dirname, '../venv/bin/python');
      const scriptPath = path.join(__dirname, '../agents/langgraph_agent.py');
      
      // Check if virtual environment exists, fallback to python3 if not
      const pythonCommand = fs.existsSync(pythonPath) ? pythonPath : 'python3';
      
      const args = [scriptPath];
      if (commitHash) {
        args.push(commitHash);
      }
      
      logToFile(`Spawning Python process: ${pythonCommand} ${args.join(' ')}`);
      
      const pythonProcess = spawn(pythonCommand, args, {
        cwd: path.join(__dirname, '..'),
        env: { ...process.env }
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
    const brainliftDir = path.join(__dirname, '../brainlifts');
    const contextDir = path.join(__dirname, '../context_logs');
    
    // Get latest files from each directory
    const latestBrainlift = await getLatestFile(brainliftDir);
    const latestContext = await getLatestFile(contextDir);
    
    return {
      brainlift: latestBrainlift,
      context: latestContext
    };
  } catch (error) {
    logToFile(`Error getting latest files: ${error.message}`);
    return {
      brainlift: null,
      context: null
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