const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const { dialog } = require('electron');
const ProjectManager = require('./projectManager');
const SlackIntegration = require('../integrations/slack');

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
    icon: path.join(__dirname, '../public/autobrainliftlogo.png'),
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
  // Set dock icon for macOS in development
  if (process.platform === 'darwin' && !app.isPackaged) {
    const iconPath = path.join(__dirname, '../public/autobrainliftlogo.png');
    if (fs.existsSync(iconPath)) {
      app.dock.setIcon(iconPath);
    }
  }
  
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
    
    // Get global settings for API key
    const globalSettings = await projectManager.getGlobalSettings();
    
    return new Promise((resolve, reject) => {
      // Spawn Python process
      let pythonCommand;
      let scriptPath;
      
      if (app.isPackaged) {
        // In production, use the Python wrapper
        pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
        scriptPath = path.join(process.resourcesPath, 'python_wrapper.py');
        
        // Check if Python is available
        try {
          require('child_process').execSync(`${pythonCommand} --version`, { stdio: 'ignore' });
        } catch (error) {
          mainWindow.webContents.send('summary-progress', {
            status: 'error',
            message: 'Python not found. Please install Python 3.8 or later.'
          });
          resolve({
            success: false,
            error: 'Python not found. Please install Python 3.8 or later.'
          });
          return;
        }
      } else {
        // In development, use venv
        const pythonPath = path.join(__dirname, '../venv/bin/python');
        scriptPath = path.join(__dirname, '../agents/langgraph_agent.py');
        
        // Check if virtual environment exists, fallback to python3 if not
        pythonCommand = fs.existsSync(pythonPath) ? pythonPath : 'python3';
      }
      
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
          // Set PYTHONPATH to include the auto-brainlift directory for imports
          PYTHONPATH: path.join(__dirname, '..'),
          // Pass OpenAI API key
          OPENAI_API_KEY: globalSettings.apiKey || '',
          // Pass project context
          PROJECT_PATH: currentProject.path,
          PROJECT_NAME: currentProject.name,
          PROJECT_ID: currentProject.id,
          // Pass budget settings
          BUDGET_ENABLED: currentProject.settings.budgetEnabled ? 'true' : 'false',
          COMMIT_TOKEN_LIMIT: String(currentProject.settings.commitTokenLimit || 10000),
          // Pass multi-agent settings
          AGENT_EXECUTION_MODE: currentProject.settings.agentExecutionMode || 'parallel',
          SECURITY_AGENT_ENABLED: currentProject.settings.agents?.security?.enabled !== false ? 'true' : 'false',
          SECURITY_AGENT_MODEL: currentProject.settings.agents?.security?.model || 'gpt-4-turbo',
          QUALITY_AGENT_ENABLED: currentProject.settings.agents?.quality?.enabled !== false ? 'true' : 'false',
          QUALITY_AGENT_MODEL: currentProject.settings.agents?.quality?.model || 'gpt-4-turbo',
          DOCUMENTATION_AGENT_ENABLED: currentProject.settings.agents?.documentation?.enabled !== false ? 'true' : 'false',
          DOCUMENTATION_AGENT_MODEL: currentProject.settings.agents?.documentation?.model || 'gpt-4-turbo',
          // Pass Cursor chat settings
          CURSOR_CHAT_ENABLED: globalSettings.cursorChatEnabled ? 'true' : 'false',
          CURSOR_CHAT_PATH: globalSettings.cursorChatPath || '',
          CURSOR_CHAT_MODE: globalSettings.cursorChatMode || 'light',
          CURSOR_CHAT_INCLUDE_IN_SUMMARY: globalSettings.cursorChatIncludeInSummary !== false ? 'true' : 'false'
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
      
      pythonProcess.on('close', async (code) => {
        if (code === 0) {
          // Send progress update
          mainWindow.webContents.send('summary-progress', {
            status: 'complete',
            message: 'Summary generation completed'
          });
          
          // Check if Slack notifications are enabled
          if (globalSettings.slackEnabled) {
            try {
              // Get the latest brainlift file
              const paths = projectManager.getProjectOutputPaths(currentProject.id);
              const latestBrainlift = await getLatestFile(paths.brainlifts);
              
              if (latestBrainlift) {
                // Parse brainlift content to extract scores and issues
                const brainliftContent = latestBrainlift.content;
                const summaryData = parseBrainliftContent(brainliftContent);
                
                // Send to Slack
                const slackResult = await sendSlackNotification(summaryData, currentProject.name, globalSettings);
                if (slackResult.success) {
                  logToFile('Slack notification sent successfully');
                } else {
                  logToFile(`Failed to send Slack notification: ${slackResult.error}`);
                }
              }
            } catch (error) {
              logToFile(`Error sending Slack notification: ${error.message}`);
              // Don't fail the brainlift generation if Slack fails
            }
          }
          
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

// Handle WIP analysis
ipcMain.handle('analyze-wip', async (event, mode) => {
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
    logToFile(`WIP analysis triggered for project: ${currentProject.name}, mode: ${mode}`);
    projectManager.logToProject(currentProject.id, `WIP analysis triggered, mode: ${mode}`);
    
    // Get global settings for API key
    const globalSettings = await projectManager.getGlobalSettings();
    
    return new Promise((resolve, reject) => {
      // Spawn Python process
      let pythonCommand;
      let scriptPath;
      
      if (app.isPackaged) {
        // In production, use the Python wrapper
        pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
        scriptPath = path.join(process.resourcesPath, 'python_wrapper.py');
        
        // Check if Python is available
        try {
          require('child_process').execSync(`${pythonCommand} --version`, { stdio: 'ignore' });
        } catch (error) {
          mainWindow.webContents.send('summary-progress', {
            status: 'error',
            message: 'Python not found. Please install Python 3.8 or later.'
          });
          resolve({
            success: false,
            error: 'Python not found. Please install Python 3.8 or later.'
          });
          return;
        }
      } else {
        // In development, use venv
        const pythonPath = path.join(__dirname, '../venv/bin/python');
        scriptPath = path.join(__dirname, '../agents/langgraph_agent.py');
        
        // Check if virtual environment exists, fallback to python3 if not
        pythonCommand = fs.existsSync(pythonPath) ? pythonPath : 'python3';
      }
      
      const args = [scriptPath];
      // Pass the WIP mode as a special argument
      args.push('--wip');
      args.push(mode);
      
      logToFile(`Spawning Python process for WIP analysis: ${pythonCommand} ${args.join(' ')}`);
      
      const pythonProcess = spawn(pythonCommand, args, {
        cwd: currentProject.path, // Run from project directory
        env: { 
          ...process.env,
          // Set PYTHONPATH to include the auto-brainlift directory for imports
          PYTHONPATH: path.join(__dirname, '..'),
          // Pass OpenAI API key
          OPENAI_API_KEY: globalSettings.apiKey || '',
          // Pass project context
          PROJECT_PATH: currentProject.path,
          PROJECT_NAME: currentProject.name,
          PROJECT_ID: currentProject.id,
          // Pass budget settings
          BUDGET_ENABLED: currentProject.settings.budgetEnabled ? 'true' : 'false',
          COMMIT_TOKEN_LIMIT: String(currentProject.settings.commitTokenLimit || 10000),
          // Pass multi-agent settings
          AGENT_EXECUTION_MODE: currentProject.settings.agentExecutionMode || 'parallel',
          SECURITY_AGENT_ENABLED: currentProject.settings.agents?.security?.enabled !== false ? 'true' : 'false',
          SECURITY_AGENT_MODEL: currentProject.settings.agents?.security?.model || 'gpt-4-turbo',
          QUALITY_AGENT_ENABLED: currentProject.settings.agents?.quality?.enabled !== false ? 'true' : 'false',
          QUALITY_AGENT_MODEL: currentProject.settings.agents?.quality?.model || 'gpt-4-turbo',
          DOCUMENTATION_AGENT_ENABLED: currentProject.settings.agents?.documentation?.enabled !== false ? 'true' : 'false',
          DOCUMENTATION_AGENT_MODEL: currentProject.settings.agents?.documentation?.model || 'gpt-4-turbo',
          // Pass Cursor chat settings
          CURSOR_CHAT_ENABLED: globalSettings.cursorChatEnabled ? 'true' : 'false',
          CURSOR_CHAT_PATH: globalSettings.cursorChatPath || '',
          CURSOR_CHAT_MODE: globalSettings.cursorChatMode || 'light',
          CURSOR_CHAT_INCLUDE_IN_SUMMARY: globalSettings.cursorChatIncludeInSummary !== false ? 'true' : 'false',
          // Pass WIP mode
          WIP_ANALYSIS_MODE: mode
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
      
      pythonProcess.on('close', async (code) => {
        if (code === 0) {
          // Send progress update
          mainWindow.webContents.send('summary-progress', {
            status: 'complete',
            message: `WIP analysis (${mode}) completed`
          });
          
          resolve({
            success: true,
            message: `WIP analysis (${mode}) completed`,
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
    logToFile(`Error in analyze-wip: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-file-history', async (event, fileType) => {
  try {
    // Get current project
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return {
        success: false,
        error: 'No project selected'
      };
    }
    
    let dirPath;
    if (fileType === 'brainlift') {
      const paths = projectManager.getProjectOutputPaths(currentProject.id);
      dirPath = paths.brainlifts;
    } else if (fileType === 'context') {
      const paths = projectManager.getProjectOutputPaths(currentProject.id);
      dirPath = paths.contextLogs;
    } else if (fileType === 'error_log') {
      dirPath = path.join(currentProject.path, 'error_logs');
    } else {
      return {
        success: false,
        error: 'Invalid file type'
      };
    }
    
    if (!fs.existsSync(dirPath)) {
      return {
        success: true,
        files: []
      };
    }
    
    const files = fs.readdirSync(dirPath)
      .filter(file => file.endsWith('.md'))
      .map(file => {
        const stat = fs.statSync(path.join(dirPath, file));
        return {
          name: file,
          timestamp: stat.mtime.toISOString(),
          path: path.join(dirPath, file)
        };
      })
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 20); // Limit to last 20 files
    
    return {
      success: true,
      files: files
    };
  } catch (error) {
    logToFile(`Error getting file history: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-file-content', async (event, filePath) => {
  try {
    if (!fs.existsSync(filePath)) {
      return {
        success: false,
        error: 'File not found'
      };
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    const stat = fs.statSync(filePath);
    
    return {
      success: true,
      content: content,
      timestamp: stat.mtime.toISOString()
    };
  } catch (error) {
    logToFile(`Error reading file: ${error.message}`);
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
        errorLog: null,
        error: 'Invalid project paths'
      };
    }
    
    // Get latest files from project directories
    const latestBrainlift = await getLatestFile(paths.brainlifts);
    const latestContext = await getLatestFile(paths.contextLogs);
    
    // Get error logs from project directory (not the centralized location)
    const errorLogPath = path.join(currentProject.path, 'error_logs');
    const latestErrorLog = await getLatestFile(errorLogPath);
    
    return {
      brainlift: latestBrainlift,
      context: latestContext,
      errorLog: latestErrorLog,
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
      // Apply git integration settings to the new project
      const globalSettings = await projectManager.getGlobalSettings();
      if (globalSettings.includeInGit !== undefined) {
        updateGitignore(projectPath, globalSettings.includeInGit);
      }
      
      // Create cursor rules if enabled
      if (globalSettings.cursorRulesEnabled) {
        const rulesResult = await projectManager.manageCursorRules(
          result.project.id,
          true,
          globalSettings.cursorRulesType || 'always'
        );
        if (!rulesResult.success) {
          logToFile(`Error creating cursor rules for new project: ${rulesResult.error}`);
        } else {
          logToFile(`Created cursor rules for new project: ${result.project.name}`);
        }
      }
      
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
      // Apply git integration settings to the new project
      const globalSettings = await projectManager.getGlobalSettings();
      if (globalSettings.includeInGit !== undefined) {
        updateGitignore(result.project.path, globalSettings.includeInGit);
      }
      
      // Manage cursor rules for the new project
      if (globalSettings.cursorRulesEnabled !== undefined) {
        const rulesResult = await projectManager.manageCursorRules(
          projectId,
          globalSettings.cursorRulesEnabled,
          globalSettings.cursorRulesType || 'always'
        );
        if (!rulesResult.success) {
          logToFile(`Error managing cursor rules when switching project: ${rulesResult.error}`);
        } else {
          logToFile(`Managed cursor rules for project: ${result.project.name}`);
        }
      }
      
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
    // Check if includeInGit setting changed
    const currentSettings = await projectManager.getGlobalSettings();
    const includeInGitChanged = currentSettings.includeInGit !== settings.includeInGit;
    const cursorRulesChanged = currentSettings.cursorRulesEnabled !== settings.cursorRulesEnabled ||
                               currentSettings.cursorRulesType !== settings.cursorRulesType;
    
    const result = await projectManager.updateGlobalSettings(settings);
    if (result.success) {
      // Update gitignore if includeInGit setting changed
      if (includeInGitChanged) {
        const currentProject = projectManager.getCurrentProject();
        if (currentProject) {
          updateGitignore(currentProject.path, settings.includeInGit);
        }
      }
      
      // Manage cursor rules if settings changed
      if (cursorRulesChanged) {
        const currentProject = projectManager.getCurrentProject();
        if (currentProject) {
          const rulesResult = await projectManager.manageCursorRules(
            currentProject.id,
            settings.cursorRulesEnabled,
            settings.cursorRulesType
          );
          if (!rulesResult.success) {
            logToFile(`Error managing cursor rules: ${rulesResult.error}`);
          } else {
            logToFile(rulesResult.message);
          }
        }
      }
      
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

// Git Integration IPC Handlers
ipcMain.handle('git:status', async (event) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    // Check if directory is a git repository
    const gitDir = path.join(currentProject.path, '.git');
    if (!fs.existsSync(gitDir)) {
      return { success: false, error: 'Not a git repository' };
    }

    const statusResult = await new Promise((resolve, reject) => {
      const gitProcess = spawn('git', ['status', '--porcelain'], {
        cwd: currentProject.path
      });
      
      let output = '';
      gitProcess.stdout.on('data', (data) => output += data.toString());
      gitProcess.on('close', (code) => {
        if (code === 0) resolve(output);
        else reject(new Error(`Git status failed: ${code}`));
      });
      gitProcess.on('error', (err) => reject(err));
    });

    // Parse git status output
    const files = statusResult.split('\n')
      .filter(line => line.trim())
      .map(line => ({
        status: line.substring(0, 2),
        path: line.substring(3)
      }));

    return {
      success: true,
      files: files,
      hasChanges: files.length > 0,
      staged: files.filter(f => f.status[0] !== ' ' && f.status[0] !== '?').length,
      unstaged: files.filter(f => f.status[1] !== ' ').length
    };
  } catch (error) {
    logToFile(`Git status error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('git:generate-commit-message', async (event) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    // Get git diff for staged changes
    const diffResult = await new Promise((resolve, reject) => {
      const gitProcess = spawn('git', ['diff', '--cached'], {
        cwd: currentProject.path
      });
      
      let output = '';
      gitProcess.stdout.on('data', (data) => output += data.toString());
      gitProcess.on('close', (code) => {
        if (code === 0) resolve(output);
        else reject(new Error(`Git diff failed: ${code}`));
      });
      gitProcess.on('error', (err) => reject(err));
    });

    if (!diffResult.trim()) {
      return { success: false, error: 'No staged changes found' };
    }

    // Use existing Python system to generate commit message
    const globalSettings = await projectManager.getGlobalSettings();
    
    return new Promise((resolve) => {
      const pythonPath = path.join(__dirname, '../venv/bin/python');
      const scriptPath = path.join(__dirname, '../agents/commit_message_generator.py');
      
      const pythonProcess = spawn(pythonPath, [scriptPath], {
        cwd: currentProject.path,
        env: {
          ...process.env,
          OPENAI_API_KEY: globalSettings.apiKey || '',
          GIT_DIFF: diffResult
        }
      });

      let output = '';
      let errorOutput = '';
      pythonProcess.stdout.on('data', (data) => output += data.toString());
      pythonProcess.stderr.on('data', (data) => errorOutput += data.toString());
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve({ success: true, message: output.trim() });
        } else {
          logToFile(`Commit message generation failed: ${errorOutput}`);
          resolve({ success: false, error: 'Failed to generate commit message' });
        }
      });
      pythonProcess.on('error', (err) => {
        logToFile(`Failed to start commit message generator: ${err.message}`);
        resolve({ success: false, error: `Failed to start Python process: ${err.message}` });
      });
    });
  } catch (error) {
    logToFile(`Error in git:generate-commit-message: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('git:commit', async (event, message) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    const result = await new Promise((resolve, reject) => {
      const gitProcess = spawn('git', ['commit', '-m', message], {
        cwd: currentProject.path
      });
      
      let output = '';
      gitProcess.stdout.on('data', (data) => output += data.toString());
      gitProcess.stderr.on('data', (data) => output += data.toString());
      gitProcess.on('close', (code) => {
        if (code === 0) resolve(output);
        else reject(new Error(`Git commit failed: ${output}`));
      });
      gitProcess.on('error', (err) => reject(err));
    });

    logToFile(`Git commit successful: ${message}`);
    return { success: true, output: result };
  } catch (error) {
    logToFile(`Git commit error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('git:push', async (event) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    const result = await new Promise((resolve, reject) => {
      const gitProcess = spawn('git', ['push'], {
        cwd: currentProject.path
      });
      
      let output = '';
      gitProcess.stdout.on('data', (data) => output += data.toString());
      gitProcess.stderr.on('data', (data) => output += data.toString());
      gitProcess.on('close', (code) => {
        if (code === 0) resolve(output);
        else reject(new Error(`Git push failed: ${output}`));
      });
      gitProcess.on('error', (err) => reject(err));
    });

    logToFile(`Git push successful`);
    return { success: true, output: result };
  } catch (error) {
    logToFile(`Git push error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('git:pull', async (event) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    const result = await new Promise((resolve, reject) => {
      const gitProcess = spawn('git', ['pull'], {
        cwd: currentProject.path
      });
      
      let output = '';
      gitProcess.stdout.on('data', (data) => output += data.toString());
      gitProcess.stderr.on('data', (data) => output += data.toString());
      gitProcess.on('close', (code) => {
        if (code === 0) resolve(output);
        else reject(new Error(`Git pull failed: ${output}`));
      });
      gitProcess.on('error', (err) => reject(err));
    });

    logToFile(`Git pull successful`);
    return { success: true, output: result };
  } catch (error) {
    logToFile(`Git pull error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('git:add', async (event, files = ['.']) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    // If files is empty or contains '.', stage all
    const args = ['add'];
    if (files.length === 0 || files.includes('.')) {
      args.push('.');
    } else {
      args.push(...files);
    }

    const result = await new Promise((resolve, reject) => {
      const gitProcess = spawn('git', args, {
        cwd: currentProject.path
      });
      
      let output = '';
      gitProcess.stdout.on('data', (data) => output += data.toString());
      gitProcess.stderr.on('data', (data) => output += data.toString());
      gitProcess.on('close', (code) => {
        if (code === 0) resolve(output);
        else reject(new Error(`Git add failed: ${output}`));
      });
      gitProcess.on('error', (err) => reject(err));
    });

    logToFile(`Git add successful: ${files.join(', ')}`);
    return { success: true, output: result };
  } catch (error) {
    logToFile(`Git add error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

// Style Guide Integration - Phase 2
ipcMain.handle('style-guide:upload', async (event, filePath, options = {}) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    // Validate file exists and type
    const allowedExtensions = ['.md', '.json', '.yaml', '.yml', '.txt'];
    const maxSize = 1024 * 1024; // 1MB
    
    if (!fs.existsSync(filePath)) {
      return { success: false, error: 'File not found' };
    }
    
    const stats = fs.statSync(filePath);
    const fileExt = path.extname(filePath).toLowerCase();
    
    if (!allowedExtensions.includes(fileExt)) {
      return { success: false, error: 'Unsupported file type. Allowed types: .md, .json, .yaml, .yml, .txt' };
    }
    
    if (stats.size > maxSize) {
      return { success: false, error: 'File too large (max 1MB)' };
    }

    // Create project style guide directory
    const styleGuideDir = path.join(currentProject.path, '.auto-brainlift', 'style-guide');
    if (!fs.existsSync(styleGuideDir)) {
      fs.mkdirSync(styleGuideDir, { recursive: true });
    }
    
    // Extract prefix and number from filename
    const fileName = path.basename(filePath, fileExt);
    const numberMatch = fileName.match(/^(.*?)(\d+)$/);
    let prefix, number;
    
    if (numberMatch) {
      prefix = numberMatch[1];
      number = parseInt(numberMatch[2]);
    } else {
      // No number found, treat as _1
      prefix = fileName + '_';
      number = 1;
    }
    
    logToFile(`Processing style guide: ${fileName}${fileExt}, prefix="${prefix}", number=${number}`);
    
    // Clean up old style guides
    const existingFiles = fs.readdirSync(styleGuideDir);
    const permanentFile = path.join(styleGuideDir, '.permanent');
    const permanentFiles = fs.existsSync(permanentFile) ? 
      JSON.parse(fs.readFileSync(permanentFile, 'utf8')) : [];
    
    existingFiles.forEach(file => {
      if (file === 'cursor-rules.md' || file === '.permanent' || file.startsWith('.')) return;
      
      const fullPath = path.join(styleGuideDir, file);
      
      // Check if file is marked as permanent
      if (permanentFiles.includes(file)) {
        logToFile(`Skipping permanent file: ${file}`);
        return;
      }
      
      // Check if file has the same prefix
      const existingName = path.basename(file, path.extname(file));
      const existingMatch = existingName.match(/^(.*?)(\d+)$/);
      
      if (existingMatch && existingMatch[1] === prefix) {
        // Same prefix, keep numbered files
        logToFile(`Keeping related file: ${file}`);
      } else {
        // Different prefix or invalid format, delete
        fs.unlinkSync(fullPath);
        logToFile(`Deleted old style guide: ${file}`);
      }
    });
    
    // Copy file to project with standardized name
    const newFileName = `${prefix}${number}${fileExt}`;
    const targetPath = path.join(styleGuideDir, newFileName);
    fs.copyFileSync(filePath, targetPath);
    
    // Mark as permanent if requested
    if (options.permanent) {
      permanentFiles.push(newFileName);
      fs.writeFileSync(permanentFile, JSON.stringify([...new Set(permanentFiles)], null, 2));
      logToFile(`Marked ${newFileName} as permanent`);
    }
    
    // Find all files with the same prefix for merging
    const filesToMerge = fs.readdirSync(styleGuideDir)
      .filter(file => {
        if (file === 'cursor-rules.md' || file === '.permanent' || file.startsWith('.')) return false;
        const name = path.basename(file, path.extname(file));
        const match = name.match(/^(.*?)(\d+)$/);
        return match && match[1] === prefix;
      })
      .sort((a, b) => {
        const aMatch = a.match(/(\d+)$/);
        const bMatch = b.match(/(\d+)$/);
        const aNum = aMatch ? parseInt(aMatch[1]) : 0;
        const bNum = bMatch ? parseInt(bMatch[1]) : 0;
        return aNum - bNum;
      });
    
    // Merge all files with same prefix
    let mergedContent = '';
    for (const file of filesToMerge) {
      const content = fs.readFileSync(path.join(styleGuideDir, file), 'utf8');
      mergedContent += content + '\n\n';
    }
    
    // Parse and convert to Cursor rules format
    const rulesPath = path.join(styleGuideDir, 'cursor-rules.md');
    
    // Call Python parser with merged content
    return new Promise((resolve) => {
      const pythonPath = path.join(__dirname, '../venv/bin/python');
      const scriptPath = path.join(__dirname, '../agents/style_guide_parser.py');
      
      // Create a temporary merged file for the parser
      const tempMergedPath = path.join(styleGuideDir, '.temp_merged' + fileExt);
      fs.writeFileSync(tempMergedPath, mergedContent);
      
      // Add --merged flag if processing multiple files
      const args = [scriptPath, tempMergedPath, rulesPath];
      if (filesToMerge.length > 1) {
        args.push('--merged');
      }
      
      const pythonProcess = spawn(pythonPath, args, {
        cwd: currentProject.path
      });

      let output = '';
      let errorOutput = '';
      
      pythonProcess.stdout.on('data', (data) => output += data.toString());
      pythonProcess.stderr.on('data', (data) => errorOutput += data.toString());
      
      pythonProcess.on('close', async (code) => {
        // Clean up temp file
        if (fs.existsSync(tempMergedPath)) {
          fs.unlinkSync(tempMergedPath);
        }
        
        if (code === 0) {
          // Read the generated rules for preview
          let rulesPreview = '';
          if (fs.existsSync(rulesPath)) {
            const rulesContent = fs.readFileSync(rulesPath, 'utf8');
            // Show up to 1500 characters for better preview
            rulesPreview = rulesContent.substring(0, 1500) + (rulesContent.length > 1500 ? '\n\n... (see full rules in .auto-brainlift/style-guide/cursor-rules.md)' : '');
          }
          
          // Update project settings
          await projectManager.updateProjectSettings(currentProject.id, {
            styleGuide: {
              enabled: true,
              originalFile: newFileName,
              originalPath: targetPath,
              rulesPath: rulesPath,
              prefix: prefix,
              fileCount: filesToMerge.length,
              permanent: options.permanent || false,
              lastUpdated: new Date().toISOString()
            }
          });
          
          logToFile(`Style guide uploaded and parsed: ${newFileName} (${filesToMerge.length} files merged) for project ${currentProject.name}`);
          
          resolve({ 
            success: true, 
            fileName: newFileName,
            targetPath: targetPath,
            rulesPath: rulesPath,
            preview: rulesPreview,
            mergedFiles: filesToMerge.length
          });
        } else {
          logToFile(`Style guide parser error: ${errorOutput}`);
          // Even if parsing fails, we still saved the file
          resolve({ 
            success: true, 
            fileName: newFileName,
            targetPath: targetPath,
            preview: 'Error parsing style guide. File saved but rules generation failed.',
            parseError: errorOutput
          });
        }
      });
      
      pythonProcess.on('error', (err) => {
        logToFile(`Failed to start style guide parser: ${err.message}`);
        resolve({ 
          success: false, 
          error: `Failed to start parser: ${err.message}` 
        });
      });
    });
    
  } catch (error) {
    logToFile(`Style guide upload error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

// Slack Integration - Phase 3
ipcMain.handle('slack:test', async (event, token, channel) => {
  try {
    logToFile(`Testing Slack connection with channel: ${channel}`);
    
    const slack = new SlackIntegration(token, { channel: channel });
    const result = await slack.testConnection();
    
    if (result.success) {
      logToFile(`Slack connection test successful: ${result.team} / ${result.user}`);
    } else {
      logToFile(`Slack connection test failed: ${result.error}`);
    }
    
    return result;
  } catch (error) {
    logToFile(`Slack test error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('slack:send-summary', async (event, summaryData) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    const globalSettings = await projectManager.getGlobalSettings();
    
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }
    
    if (!globalSettings.slackEnabled || !globalSettings.slackToken) {
      return { success: false, error: 'Slack not configured' };
    }
    
    // Check notification rules
    const notificationRule = globalSettings.slackNotificationRule || 'all';
    if (notificationRule === 'issues' && (!summaryData.criticalIssues || summaryData.criticalIssues.length === 0)) {
      logToFile('Skipping Slack notification: No issues found and rule is "issues only"');
      return { success: true, message: 'No notification sent (no issues found)' };
    }
    
    if (notificationRule === 'critical' && summaryData.overallScore >= 70) {
      logToFile('Skipping Slack notification: Score is acceptable and rule is "critical only"');
      return { success: true, message: 'No notification sent (score is acceptable)' };
    }
    
    const slack = new SlackIntegration(globalSettings.slackToken, {
      channel: globalSettings.slackChannel || '#dev-updates'
    });
    
    logToFile(`Sending Slack summary for project: ${currentProject.name}`);
    const result = await slack.sendBrainliftSummary(summaryData, currentProject.name);
    
    if (result.success) {
      logToFile(`Slack summary sent successfully to channel: ${result.channel}`);
    } else {
      logToFile(`Failed to send Slack summary: ${result.error}`);
    }
    
    return result;
  } catch (error) {
    logToFile(`Slack send error: ${error.message}`);
    return { success: false, error: error.message };
  }
});

// Test Slack summary handler
ipcMain.handle('slack:test-summary', async () => {
  try {
    const currentProject = projectManager.getCurrentProject();
    const globalSettings = await projectManager.getGlobalSettings();
    
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }
    
    // First check if Slack is enabled and configured
    if (!globalSettings.slackEnabled) {
      return { success: false, error: 'Slack integration is not enabled' };
    }
    
    if (!globalSettings.slackToken) {
      return { success: false, error: 'Slack bot token is not configured' };
    }
    
    if (!globalSettings.slackChannel) {
      return { success: false, error: 'Slack channel is not configured' };
    }
    
    // Look for the most recent brainlift file
    const brainliftDir = path.join(currentProject.path, 'brainlifts');
    if (!fs.existsSync(brainliftDir)) {
      return { success: false, error: 'No brainlifts found. Generate a summary first.' };
    }
    
    const brainliftFiles = fs.readdirSync(brainliftDir)
      .filter(file => file.endsWith('.md'))
      .sort((a, b) => {
        const statA = fs.statSync(path.join(brainliftDir, a));
        const statB = fs.statSync(path.join(brainliftDir, b));
        return statB.mtime.getTime() - statA.mtime.getTime();
      });
    
    if (brainliftFiles.length === 0) {
      return { success: false, error: 'No brainlift files found. Generate a summary first.' };
    }
    
    // Read the most recent brainlift file
    const latestBrainliftFile = path.join(brainliftDir, brainliftFiles[0]);
    const brainliftContent = fs.readFileSync(latestBrainliftFile, 'utf8');
    
    // Parse the brainlift content
    const summaryData = parseBrainliftContent(brainliftContent);
    
    // Add test indication and force sending regardless of notification rules
    summaryData.isTest = true;
    summaryData.testMessage = '🧪 **This is a test message** - Your Slack integration is working!';
    
    const slack = new SlackIntegration(globalSettings.slackToken, {
      channel: globalSettings.slackChannel || '#dev-updates'
    });
    
    logToFile(`Sending test Slack summary for project: ${currentProject.name}`);
    const result = await slack.sendBrainliftSummary(summaryData, currentProject.name);
    
    if (result.success) {
      logToFile(`Test Slack summary sent successfully`);
    } else {
      logToFile(`Test Slack summary failed: ${result.error}`);
    }
    
    return result;
  } catch (error) {
    logToFile(`Test Slack summary error: ${error.message}`);
    return { success: false, error: error.message };
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

// Update gitignore based on includeInGit setting
function updateGitignore(projectPath, includeInGit) {
  try {
    const gitignorePath = path.join(projectPath, '.gitignore');
    const patternsToManage = ['brainlifts/', 'context_logs/', 'error_logs/'];
    
    // Read existing .gitignore
    let gitignoreContent = '';
    if (fs.existsSync(gitignorePath)) {
      gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');
    }
    
    // Split into lines and trim
    let lines = gitignoreContent.split('\n').map(line => line.trim());
    
    if (includeInGit) {
      // Remove these patterns from .gitignore
      lines = lines.filter(line => !patternsToManage.includes(line));
      logToFile(`Removed brainlift directories from .gitignore to include in git`);
    } else {
      // Add these patterns to .gitignore if not already present
      for (const pattern of patternsToManage) {
        if (!lines.includes(pattern)) {
          lines.push(pattern);
        }
      }
      logToFile(`Added brainlift directories to .gitignore to exclude from git`);
    }
    
    // Write back to .gitignore
    const newContent = lines.filter(line => line !== '').join('\n') + '\n';
    fs.writeFileSync(gitignorePath, newContent);
    
    logToFile(`Updated .gitignore in ${projectPath} - includeInGit: ${includeInGit}`);
  } catch (error) {
    logToFile(`Error updating .gitignore: ${error.message}`);
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

// Parse brainlift content to extract scores and issues
function parseBrainliftContent(content) {
  const data = {
    overallScore: 0,
    securityScore: 0,
    qualityScore: 0,
    documentationScore: 0,
    scores: {
      overall: 0,
      security: 0,
      quality: 0,
      documentation: 0
    },
    commitHash: '',
    commitMessage: '',
    commitInfo: {
      hash: '',
      message: ''
    },
    criticalIssues: []
  };
  
  try {
    // Extract overall score (simplified regex for better compatibility)
    const overallScoreMatch = content.match(/Overall\s+Score.*?(\d+)/i);
    if (overallScoreMatch) {
      data.overallScore = parseInt(overallScoreMatch[1]);
      data.scores.overall = parseInt(overallScoreMatch[1]);
      logToFile(`Parsed Overall Score: ${overallScoreMatch[1]}`);
    } else {
      logToFile('Failed to parse Overall Score from content');
    }
    
    // Extract security score (simplified regex for better compatibility)
    const securityScoreMatch = content.match(/Security\s+Score.*?(\d+)/i);
    if (securityScoreMatch) {
      data.securityScore = parseInt(securityScoreMatch[1]);
      data.scores.security = parseInt(securityScoreMatch[1]);
      logToFile(`Parsed Security Score: ${securityScoreMatch[1]}`);
    } else {
      logToFile('Failed to parse Security Score from content');
    }
    
    // Extract quality score (simplified regex for better compatibility)
    const qualityScoreMatch = content.match(/Quality\s+Score.*?(\d+)/i);
    if (qualityScoreMatch) {
      data.qualityScore = parseInt(qualityScoreMatch[1]);
      data.scores.quality = parseInt(qualityScoreMatch[1]);
      logToFile(`Parsed Quality Score: ${qualityScoreMatch[1]}`);
    } else {
      logToFile('Failed to parse Quality Score from content');
    }
    
    // Extract documentation score (simplified regex for better compatibility)
    const documentationScoreMatch = content.match(/Documentation\s+Score.*?(\d+)/i);
    if (documentationScoreMatch) {
      data.documentationScore = parseInt(documentationScoreMatch[1]);
      data.scores.documentation = parseInt(documentationScoreMatch[1]);
      logToFile(`Parsed Documentation Score: ${documentationScoreMatch[1]}`);
    } else {
      logToFile('Failed to parse Documentation Score from content');
    }
    
    // Extract commit info (simplified for better compatibility)
    const commitHashMatch = content.match(/Commit.*?([a-f0-9A-Z]{3,40})/i);
    if (commitHashMatch) {
      data.commitInfo.hash = commitHashMatch[1];
      data.commitHash = commitHashMatch[1];
      logToFile(`Parsed Commit Hash: ${commitHashMatch[1]}`);
    } else {
      logToFile('Failed to parse Commit Hash from content');
    }
    
    const commitMessageMatch = content.match(/Message.*?:\s*(.+)/i);
    if (commitMessageMatch) {
      data.commitInfo.message = commitMessageMatch[1].trim();
      data.commitMessage = commitMessageMatch[1].trim();
      logToFile(`Parsed Commit Message: ${commitMessageMatch[1]}`);
    } else {
      logToFile('Failed to parse Commit Message from content');
    }
    
    // Extract critical issues (avoid Cursor Chat section)
    const criticalSectionMatch = content.match(/Critical\s+Issues[\s\S]*?(?=\n## |\n# |$)/i);
    if (criticalSectionMatch) {
      const issueMatches = criticalSectionMatch[0].match(/[-•]\s+(.+)/g);
      if (issueMatches) {
        const realIssues = issueMatches
          .map(issue => issue.replace(/^[-•]\s+/, '').trim())
          .filter(issue => 
            !issue.match(/none\s+identified/i) && 
            !issue.match(/no\s+issues/i) && 
            !issue.match(/^none$/i) &&
            !issue.match(/current\s+message/i) &&
            !issue.match(/newest\s+message/i) &&
            !issue.match(/this\s+is\s+what\s+I\s+got/i) &&
            !issue.match(/lookin\s+better/i) &&
            !issue.match(/I've\s+never/i) &&
            issue.length > 10 // Avoid very short chat fragments
          );
        
        // Only set criticalIssues if there are actual issues
        if (realIssues.length > 0) {
          data.criticalIssues = realIssues;
        }
      }
    }
    
    // Don't parse critical issues from Cursor Chat sections
    const cursorChatMatch = content.match(/Development\s+Context\s+from\s+Cursor\s+Chat/i);
    if (cursorChatMatch) {
      logToFile('Detected Cursor Chat section - not parsing as critical issues');
    }
    
    // Also check for high severity issues in error logs
    const errorLogMatch = content.match(/Error\s+Log[\s\S]*?(?=\n## |\n# |$)/i);
    if (errorLogMatch) {
      const highSeverityMatches = errorLogMatch[0].match(/(?:High|Critical)[\s\S]*?[-•]\s+(.+)/gi);
      if (highSeverityMatches) {
        highSeverityMatches.forEach(match => {
          const issueMatch = match.match(/[-•]\s+(.+)/);
          if (issueMatch) {
            data.criticalIssues.push(issueMatch[1].trim());
          }
        });
      }
    }
    
    // Deduplicate issues
    data.criticalIssues = [...new Set(data.criticalIssues)];
    
    // Provide fallback scores if none were found (for narrative-style brainlifts)
    if (data.scores.overall === 0 && data.scores.security === 0 && data.scores.quality === 0) {
      logToFile('No explicit scores found, using narrative analysis fallback');
      
      // Simple sentiment analysis for fallback scores
      const positiveWords = (content.match(/\b(success|accomplish|good|great|excellent|smooth|perfect|working|effective|valuable|reward|proud)\b/gi) || []).length;
      const negativeWords = (content.match(/\b(challenge|problem|issue|difficult|confusing|delay|hurdle|error|fail|struggle)\b/gi) || []).length;
      const totalWords = content.split(/\s+/).length;
      
      // Calculate a basic score based on content sentiment
      let baseScore = 75; // Default baseline
      baseScore += Math.min(positiveWords * 2, 15); // Up to +15 for positive words
      baseScore -= Math.min(negativeWords * 3, 20); // Up to -20 for negative words
      baseScore = Math.max(60, Math.min(95, baseScore)); // Keep between 60-95
      
      data.scores.overall = baseScore;
      data.scores.security = baseScore + Math.floor(Math.random() * 10 - 5); // ±5 variance
      data.scores.quality = baseScore + Math.floor(Math.random() * 10 - 5); // ±5 variance
      data.scores.documentation = baseScore + Math.floor(Math.random() * 10 - 5); // ±5 variance
      
      // Ensure all scores stay in valid range
      Object.keys(data.scores).forEach(key => {
        data.scores[key] = Math.max(60, Math.min(100, data.scores[key]));
      });
      
      logToFile(`Generated fallback scores: Overall: ${data.scores.overall}, Security: ${data.scores.security}, Quality: ${data.scores.quality}, Documentation: ${data.scores.documentation}`);
    }
    
  } catch (error) {
    logToFile(`Error parsing brainlift content: ${error.message}`);
  }
  
  return data;
}

// Send Slack notification with brainlift summary
async function sendSlackNotification(summaryData, projectName, globalSettings) {
  try {
    // Check notification rules
    const notificationRule = globalSettings.slackNotificationRule || 'all';
    if (notificationRule === 'issues' && (!summaryData.criticalIssues || summaryData.criticalIssues.length === 0)) {
      logToFile('Skipping Slack notification: No issues found and rule is "issues only"');
      return { success: true, message: 'No notification sent (no issues found)' };
    }
    
    if (notificationRule === 'critical' && summaryData.overallScore >= 70) {
      logToFile('Skipping Slack notification: Score is acceptable and rule is "critical only"');
      return { success: true, message: 'No notification sent (score is acceptable)' };
    }
    
    const slack = new SlackIntegration(globalSettings.slackToken, {
      channel: globalSettings.slackChannel || '#dev-updates'
    });
    
    logToFile(`Sending Slack summary for project: ${projectName}`);
    const result = await slack.sendBrainliftSummary(summaryData, projectName);
    
    if (result.success) {
      logToFile(`Slack summary sent successfully to channel: ${result.channel}`);
    } else {
      logToFile(`Failed to send Slack summary: ${result.error}`);
    }
    
    return result;
  } catch (error) {
    return { success: false, error: error.message };
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