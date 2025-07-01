const settings = require('electron-settings');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');
const { v4: uuidv4 } = require('uuid');

class ProjectManager {
  constructor() {
    // Initialize settings with defaults
    this.initializeSettings();
    
    // Load data from settings
    this.loadFromSettings();
  }

  async initializeSettings() {
    // Set defaults if not already set
    if (!await settings.has('projects')) {
      await settings.set('projects', {});
    }
    if (!await settings.has('currentProjectId')) {
      await settings.set('currentProjectId', null);
    }
    if (!await settings.has('globalSettings')) {
      await settings.set('globalSettings', {
        apiKey: '',
        budgetEnabled: false,
        commitTokenLimit: 10000,
        costPer1kTokens: 0.002
      });
    }
  }

  async loadFromSettings() {
    this.projects = await settings.get('projects') || {};
    this.currentProjectId = await settings.get('currentProjectId');
  }

  // Create a new project
  async createProject(projectPath, name = null) {
    try {
      // Validate path exists
      if (!fs.existsSync(projectPath)) {
        throw new Error(`Path does not exist: ${projectPath}`);
      }

      // Check if project already exists at this path
      const existingProject = Object.values(this.projects).find(p => p.path === projectPath);
      if (existingProject) {
        return {
          success: false,
          error: 'Project already exists at this path',
          project: existingProject
        };
      }

      // Generate unique ID
      const projectId = uuidv4();
      
      // Extract project name from path if not provided
      if (!name) {
        name = path.basename(projectPath);
      }

      // Create project object
      const project = {
        id: projectId,
        name: name,
        path: projectPath,
        createdAt: new Date().toISOString(),
        lastAccessedAt: new Date().toISOString(),
        lastProcessedCommit: null,
        settings: {
          budgetEnabled: false,
          commitTokenLimit: 10000,
          enabledAgents: ['brainlift', 'context']
        }
      };

      // Save to store
      this.projects[projectId] = project;
      await settings.set('projects', this.projects);

      // Create project data directory
      await this.ensureProjectDataDir(projectId);

      return {
        success: true,
        project: project
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Switch to a different project
  async switchProject(projectId) {
    if (!this.projects[projectId]) {
      return {
        success: false,
        error: 'Project not found'
      };
    }

    // Update last accessed time
    this.projects[projectId].lastAccessedAt = new Date().toISOString();
    
    // Update current project
    this.currentProjectId = projectId;
    
    // Save to store
    await settings.set('currentProjectId', projectId);
    await settings.set('projects', this.projects);

    return {
      success: true,
      project: this.projects[projectId]
    };
  }

  // Remove a project
  async removeProject(projectId) {
    if (!this.projects[projectId]) {
      return {
        success: false,
        error: 'Project not found'
      };
    }

    // Delete project data
    delete this.projects[projectId];
    
    // If this was the current project, clear it
    if (this.currentProjectId === projectId) {
      this.currentProjectId = null;
      await settings.set('currentProjectId', null);
    }

    // Save to store
    await settings.set('projects', this.projects);

    // Optionally remove project data directory
    // (keeping for now in case user wants to recover)

    return {
      success: true
    };
  }

  // Get all projects
  getAllProjects() {
    return Object.values(this.projects).sort((a, b) => 
      new Date(b.lastAccessedAt) - new Date(a.lastAccessedAt)
    );
  }

  // Get current project
  getCurrentProject() {
    if (!this.currentProjectId) {
      return null;
    }
    return this.projects[this.currentProjectId];
  }

  // Update project settings
  async updateProjectSettings(projectId, projectSettings) {
    if (!this.projects[projectId]) {
      return {
        success: false,
        error: 'Project not found'
      };
    }

    // Merge settings
    this.projects[projectId].settings = {
      ...this.projects[projectId].settings,
      ...projectSettings
    };

    // Save to store
    await settings.set('projects', this.projects);

    return {
      success: true,
      project: this.projects[projectId]
    };
  }

  // Get global settings
  async getGlobalSettings() {
    return await settings.get('globalSettings') || {
      apiKey: '',
      budgetEnabled: false,
      commitTokenLimit: 10000,
      costPer1kTokens: 0.002
    };
  }

  // Update global settings
  async updateGlobalSettings(newSettings) {
    const currentSettings = await this.getGlobalSettings();
    const updatedSettings = { ...currentSettings, ...newSettings };
    
    await settings.set('globalSettings', updatedSettings);

    return {
      success: true,
      settings: updatedSettings
    };
  }

  // Get project data directory
  getProjectDataDir(projectId) {
    const userDataPath = app.getPath('userData');
    return path.join(userDataPath, 'projects', projectId);
  }

  // Ensure project data directory exists
  async ensureProjectDataDir(projectId) {
    const projectDataDir = this.getProjectDataDir(projectId);
    const dirs = [
      projectDataDir,
      path.join(projectDataDir, 'cache'),
      path.join(projectDataDir, 'outputs')
    ];

    for (const dir of dirs) {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    }
  }

  // Get project-specific output paths
  getProjectOutputPaths(projectId) {
    const project = this.projects[projectId];
    if (!project) {
      return null;
    }

    // Use project path for outputs (maintaining backward compatibility)
    return {
      brainlifts: path.join(project.path, 'brainlifts'),
      contextLogs: path.join(project.path, 'context_logs')
    };
  }

  // Update last processed commit
  async updateLastProcessedCommit(projectId, commitHash) {
    if (!this.projects[projectId]) {
      return {
        success: false,
        error: 'Project not found'
      };
    }

    this.projects[projectId].lastProcessedCommit = commitHash;
    await settings.set('projects', this.projects);

    return {
      success: true
    };
  }

  // Log to project-specific log
  logToProject(projectId, message) {
    const projectDataDir = this.getProjectDataDir(projectId);
    const logFile = path.join(projectDataDir, 'project.log');
    
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    
    fs.appendFileSync(logFile, logMessage);
  }

  // Manage Cursor Rules for project
  async manageCursorRules(projectId, enabled, ruleType = 'always') {
    const project = this.projects[projectId];
    if (!project) {
      return {
        success: false,
        error: 'Project not found'
      };
    }

    const cursorDir = path.join(project.path, '.cursor');
    const rulesDir = path.join(cursorDir, 'rules');
    const ruleFile = path.join(rulesDir, 'auto-brainlift.mdc');

    try {
      if (enabled) {
        // Create directories if they don't exist
        if (!fs.existsSync(cursorDir)) {
          fs.mkdirSync(cursorDir, { recursive: true });
        }
        if (!fs.existsSync(rulesDir)) {
          fs.mkdirSync(rulesDir, { recursive: true });
        }

        // Create the rule content
        const ruleContent = this.generateCursorRuleContent(project.name, ruleType);
        
        // Write the rule file
        fs.writeFileSync(ruleFile, ruleContent, 'utf8');
        
        this.logToProject(projectId, `Created Cursor rules file at ${ruleFile}`);
        
        return {
          success: true,
          message: 'Cursor rules file created successfully'
        };
      } else {
        // Remove the rule file if it exists
        if (fs.existsSync(ruleFile)) {
          fs.unlinkSync(ruleFile);
          this.logToProject(projectId, `Removed Cursor rules file at ${ruleFile}`);
          
          // Clean up empty directories
          try {
            if (fs.existsSync(rulesDir) && fs.readdirSync(rulesDir).length === 0) {
              fs.rmdirSync(rulesDir);
            }
            if (fs.existsSync(cursorDir) && fs.readdirSync(cursorDir).length === 0) {
              fs.rmdirSync(cursorDir);
            }
          } catch (e) {
            // Ignore errors when cleaning up directories
          }
        }
        
        return {
          success: true,
          message: 'Cursor rules file removed successfully'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  generateCursorRuleContent(projectName, ruleType) {
    const typeConfig = {
      always: 'alwaysApply: true',
      auto: 'globs: "**/*"',
      manual: ''
    };

    return `---
description: Auto-Brainlift Project Context for ${projectName}
${typeConfig[ruleType] || typeConfig.always}
---

# Auto-Brainlift Project Assistant

This project uses Auto-Brainlift for automatic documentation and reflection generation after each git commit.

## When assisting with this codebase:

1. **Check Context Logs**: Always review the latest context logs in \`/context_logs/\` to understand:
   - Current project structure and architecture
   - Recent commits and changes
   - Technical debt and TODOs
   - Multi-agent analysis results (security, quality, documentation)
   - Active development areas

2. **Check Brainlifts**: Review \`/brainlifts/\` for developer insights:
   - Decision rationale and thought process
   - Challenges faced and solutions implemented
   - Future plans and considerations
   - Personal reflections on the code

3. **Latest Documentation**: The most recent files contain:
   - \`context_logs/YYYY-MM-DD_HH-MM-SS_context.md\`: Technical project state
   - \`brainlifts/YYYY-MM-DD_HH-MM-SS_brainlift.md\`: Developer reflections
   - \`error_logs/YYYY-MM-DD_HH-MM-SS_error_log.md\`: Issues found by agents

## Key Information Sources:

- **Project Architecture**: Found in latest context.md under "Project Structure"
- **Recent Changes**: Listed in context.md under "Recent Commits"
- **Known Issues**: Documented in error_log.md with severity levels
- **Development Context**: Cursor chat history analysis in brainlift.md

## Best Practices:

- Always consider the historical context before suggesting changes
- Reference specific insights from the documentation when relevant
- Understand the developer's thought process from brainlifts
- Be aware of identified security, quality, and documentation issues

## File Naming Convention:
All Auto-Brainlift files follow the pattern: \`YYYY-MM-DD_HH-MM-SS_[type].md\`

---

Remember: These documents provide rich context about the project's evolution, decisions, and current state. Use them to provide more informed and contextual assistance.
`;
  }
}

module.exports = ProjectManager; 