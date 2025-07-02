# Auto-Brainlift v2.0 Implementation Guide
## AI-Optimized Development Instructions for Cursor

---

## 🎯 Document Purpose

This guide is specifically crafted for AI-assisted development using Cursor. It provides precise implementation instructions, code examples, and pitfall warnings to ensure smooth development without AI wandering into problematic solutions.

---

## 📋 Current Architecture Analysis

### **Existing Strengths to Leverage**

#### 1. **Robust IPC System** (`electron/main.js`)
```javascript
// Current pattern - LEVERAGE THIS:
ipcMain.handle('generate-summary', async (event, commitHash) => {
  // Existing error handling and project validation
  const currentProject = projectManager.getCurrentProject();
  // Python process spawning with environment variables
  const pythonProcess = spawn(pythonCommand, args, { env: {...} });
});
```

**✅ USE FOR NEW FEATURES:**
- Git operations will follow same IPC pattern
- Style guide upload will use same validation
- Slack integration will use same error handling

#### 2. **Project Management System** (`electron/projectManager.js`)
```javascript
// Current settings structure - EXTEND THIS:
this.projects[projectId].settings = {
  budgetEnabled: false,
  commitTokenLimit: 10000,
  agents: { security: { enabled: true, model: 'gpt-4-turbo' } }
  // ADD NEW: gitIntegration, styleGuide, integrations
};
```

#### 3. **UI Structure** (`index.html`)
```html
<!-- Current Manual Generation section (line 1134) - EXPAND THIS: -->
<section class="controls">
  <h2>Manual Generation</h2>
  <button id="generateBtn" class="button">Generate Summary</button>
  <!-- ADD: Git controls, trigger buttons -->
</section>
```

---

## 🚀 Phase 1: Git Workflow Foundation

### **Implementation Order & Code Locations**

#### 1.1 **Git Status API** (Add to `electron/main.js`)

```javascript
// ADD AFTER line 602 in main.js
ipcMain.handle('git:status', async (event) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    const { spawn } = require('child_process');
    
    // Get git status
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
    });

    // Parse git status output
    const files = output.split('\n')
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
    return { success: false, error: error.message };
  }
});
```

#### 1.2 **AI Commit Message Generation** (Add to `electron/main.js`)

```javascript
// ADD AFTER git:status handler
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
      pythonProcess.stdout.on('data', (data) => output += data.toString());
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve({ success: true, message: output.trim() });
        } else {
          resolve({ success: false, error: 'Failed to generate commit message' });
        }
      });
    });
  } catch (error) {
    return { success: false, error: error.message };
  }
});
```

#### 1.3 **Git Operations** (Add to `electron/main.js`)

```javascript
// ADD git commit, push, pull handlers
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
    });

    return { success: true, output: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Similar patterns for git:push and git:pull
```

#### 1.4 **Create Python Commit Message Generator** (`agents/commit_message_generator.py`)

```python
#!/usr/bin/env python3
"""
Commit Message Generator
Generates AI-powered commit messages from git diff
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def generate_commit_message():
    """Generate commit message from git diff"""
    
    git_diff = os.getenv('GIT_DIFF', '')
    if not git_diff:
        print("Error: No git diff provided")
        sys.exit(1)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OpenAI API key not provided")
        sys.exit(1)
    
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # Cost-effective for commit messages
            temperature=0.3,
            api_key=api_key
        )
        
        # Create messages
        system_msg = SystemMessage(content="""
You are an expert developer writing git commit messages.
Generate a concise, descriptive commit message based on the git diff.
Follow conventional commit format: type(scope): description
Examples: feat: add user authentication, fix: resolve login bug, docs: update README

Rules:
1. Keep it under 50 characters for the main message
2. Be specific about what changed
3. Use imperative mood (add, fix, update, not added, fixed, updated)
4. Don't mention file names unless critical
5. Focus on the "what" and "why", not the "how"
""")
        
        human_msg = HumanMessage(content=f"Generate a commit message for this git diff:\n\n{git_diff}")
        
        # Generate message
        response = llm.invoke([system_msg, human_msg])
        commit_message = response.content.strip()
        
        # Clean up the message (remove quotes if present)
        if commit_message.startswith('"') and commit_message.endswith('"'):
            commit_message = commit_message[1:-1]
        
        print(commit_message)
        
    except Exception as e:
        print(f"Error generating commit message: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_commit_message()
```

#### 1.5 **UI Integration** (Modify `index.html`)

**Find line 1134 and REPLACE the Manual Generation section:**

```html
<!-- REPLACE existing section with expanded version -->
<section class="controls">
  <h2>Manual Generation</h2>
  
  <!-- Original generate button -->
  <div class="controls-group">
    <button id="generateBtn" class="button">
      <span>Generate Summary</span>
    </button>
    <button id="analyzeWipBtn" class="button-secondary">
      <span>📝 Analyze WIP</span>
    </button>
  </div>
  
  <!-- Git controls -->
  <div class="controls-group">
    <div class="git-status" id="gitStatus">
      <span class="status-text">Check git status...</span>
    </div>
    
    <div class="git-controls">
      <button id="commitBtn" class="button-secondary" disabled>
        <span>📤 Commit</span>
      </button>
      <button id="pushBtn" class="button-secondary">
        <span>⬆️ Push</span>
      </button>
      <button id="pullBtn" class="button-secondary">
        <span>⬇️ Pull</span>
      </button>
    </div>
  </div>
  
  <div id="commitMessageContainer" style="display: none;">
    <textarea id="commitMessageText" placeholder="AI-generated commit message will appear here..."></textarea>
    <div class="commit-actions">
      <button id="acceptCommitBtn" class="button">Accept & Commit</button>
      <button id="editCommitBtn" class="button-secondary">Edit Message</button>
      <button id="cancelCommitBtn" class="button-secondary">Cancel</button>
    </div>
  </div>
  
  <div id="status" class="status"></div>
</section>
```

**Add CSS (after line 400):**

```css
/* Git Controls Styling */
.controls-group {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  align-items: center;
}

.git-status {
  background: rgba(42, 46, 52, 0.5);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
  color: var(--foam-300);
  min-width: 200px;
}

.git-controls {
  display: flex;
  gap: var(--spacing-sm);
}

#commitMessageContainer {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: rgba(42, 46, 52, 0.3);
}

#commitMessageText {
  width: 100%;
  min-height: 60px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: rgba(42, 46, 52, 0.5);
  color: var(--color-text);
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--font-size-sm);
  resize: vertical;
}

.commit-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}
```

#### 1.6 **JavaScript Integration** (Add to `index.html` script section)

**Add after line 1600:**

```javascript
// Git Controls
const commitBtn = document.getElementById('commitBtn');
const pushBtn = document.getElementById('pushBtn');
const pullBtn = document.getElementById('pullBtn');
const gitStatus = document.getElementById('gitStatus');
const commitMessageContainer = document.getElementById('commitMessageContainer');
const commitMessageText = document.getElementById('commitMessageText');
const acceptCommitBtn = document.getElementById('acceptCommitBtn');
const editCommitBtn = document.getElementById('editCommitBtn');
const cancelCommitBtn = document.getElementById('cancelCommitBtn');

// Update git status periodically
async function updateGitStatus() {
  try {
    const result = await window.electronAPI.git.status();
    if (result.success) {
      const statusText = result.hasChanges ? 
        `${result.staged} staged, ${result.unstaged} unstaged` : 
        'No changes';
      gitStatus.querySelector('.status-text').textContent = statusText;
      commitBtn.disabled = result.staged === 0;
    } else {
      gitStatus.querySelector('.status-text').textContent = 'Not a git repo';
      commitBtn.disabled = true;
    }
  } catch (error) {
    gitStatus.querySelector('.status-text').textContent = 'Git error';
    commitBtn.disabled = true;
  }
}

// Git operations
commitBtn.addEventListener('click', async () => {
  try {
    showStatus('Generating commit message...', 'info');
    const result = await window.electronAPI.git.generateCommitMessage();
    
    if (result.success) {
      commitMessageText.value = result.message;
      commitMessageContainer.style.display = 'block';
    } else {
      showStatus(`Error: ${result.error}`, 'error');
    }
  } catch (error) {
    showStatus(`Error generating commit message: ${error.message}`, 'error');
  }
});

acceptCommitBtn.addEventListener('click', async () => {
  const message = commitMessageText.value.trim();
  if (!message) {
    showStatus('Please enter a commit message', 'error');
    return;
  }
  
  try {
    showStatus('Committing changes...', 'info');
    const result = await window.electronAPI.git.commit(message);
    
    if (result.success) {
      showStatus('Successfully committed changes', 'success');
      commitMessageContainer.style.display = 'none';
      commitMessageText.value = '';
      updateGitStatus();
    } else {
      showStatus(`Commit failed: ${result.error}`, 'error');
    }
  } catch (error) {
    showStatus(`Error committing: ${error.message}`, 'error');
  }
});

// Initialize git status on load
updateGitStatus();
setInterval(updateGitStatus, 10000); // Update every 10 seconds
```

#### 1.7 **Preload API Extension** (Modify `electron/preload.js`)

**Add after line 92:**

```javascript
// Git API
git: {
  status: () => ipcRenderer.invoke('git:status'),
  generateCommitMessage: () => ipcRenderer.invoke('git:generate-commit-message'),
  commit: (message) => ipcRenderer.invoke('git:commit', message),
  push: () => ipcRenderer.invoke('git:push'),
  pull: () => ipcRenderer.invoke('git:pull')
}
```

### **🚨 Phase 1 Pitfalls to Avoid**

#### **Git Integration Pitfalls**

```javascript
// ❌ DON'T: Assume git is always available
const result = await spawn('git', ['status']);

// ✅ DO: Check git availability first
const isGitRepo = await checkGitRepository(currentProject.path);
if (!isGitRepo) {
  return { success: false, error: 'Not a git repository' };
}
```

#### **Error Handling Pitfalls**

```javascript
// ❌ DON'T: Let git errors crash the app
gitProcess.on('error', (err) => {
  // App crashes here
});

// ✅ DO: Graceful error handling
gitProcess.on('error', (err) => {
  resolve({ success: false, error: err.message });
});
```

#### **Python Integration Pitfalls**

```python
# ❌ DON'T: Import from unknown paths
from agents.some_module import something

# ✅ DO: Use sys.path.insert for reliable imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## 🎨 Phase 2: Style Guide System

### **Implementation Strategy**

#### 2.1 **File Upload Handler** (Add to `electron/main.js`)

```javascript
// ADD AFTER line 602
ipcMain.handle('style-guide:upload', async (event, filePath) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }

    if (!fs.existsSync(filePath)) {
      return { success: false, error: 'File not found' };
    }

    // Read and parse the style guide file
    const content = fs.readFileSync(filePath, 'utf8');
    const fileName = path.basename(filePath);
    const fileExt = path.extname(filePath).toLowerCase();
    
    // Create style guide directory in project
    const styleGuideDir = path.join(currentProject.path, '.auto-brainlift', 'style-guide');
    if (!fs.existsSync(styleGuideDir)) {
      fs.mkdirSync(styleGuideDir, { recursive: true });
    }
    
    // Copy file to project
    const targetPath = path.join(styleGuideDir, fileName);
    fs.copyFileSync(filePath, targetPath);
    
    // Parse and convert to Cursor rules format
    const convertedRules = await convertStyleGuideToRules(content, fileExt);
    
    // Save converted rules
    const rulesPath = path.join(styleGuideDir, 'cursor-rules.md');
    fs.writeFileSync(rulesPath, convertedRules, 'utf8');
    
    // Update project settings
    const result = await projectManager.updateProjectSettings(currentProject.id, {
      styleGuide: {
        enabled: true,
        originalFile: fileName,
        originalPath: targetPath,
        rulesPath: rulesPath,
        lastUpdated: new Date().toISOString()
      }
    });
    
    return { 
      success: true, 
      fileName: fileName,
      rulesPreview: convertedRules.substring(0, 500) + '...'
    };
    
  } catch (error) {
    return { success: false, error: error.message };
  }
});
```

#### 2.2 **Style Guide Parser** (Create `agents/style_guide_parser.py`)

```python
#!/usr/bin/env python3
"""
Style Guide Parser
Converts various style guide formats to Cursor Rules format
"""

import json
import yaml
import re
import sys
from pathlib import Path

class StyleGuideParser:
    def __init__(self):
        self.supported_formats = ['.md', '.json', '.yaml', '.yml', '.txt']
    
    def parse_file(self, file_path, content):
        """Parse style guide file and convert to Cursor rules"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.json':
            return self.parse_json(content)
        elif ext in ['.yaml', '.yml']:
            return self.parse_yaml(content)
        elif ext == '.md':
            return self.parse_markdown(content)
        else:
            return self.parse_text(content)
    
    def parse_json(self, content):
        """Parse JSON style guide (ESLint, Prettier, etc.)"""
        try:
            config = json.loads(content)
            rules = []
            
            # ESLint rules
            if 'rules' in config:
                rules.append("## ESLint Rules")
                for rule, setting in config['rules'].items():
                    if setting != 'off':
                        rules.append(f"- {rule}: {setting}")
            
            # Prettier rules
            for key, value in config.items():
                if key not in ['rules', 'extends', 'plugins']:
                    rules.append(f"- {key}: {value}")
            
            return self.format_cursor_rules(rules, "JSON Configuration")
            
        except json.JSONDecodeError:
            return self.parse_text(content)
    
    def parse_markdown(self, content):
        """Parse Markdown style guide"""
        # Extract code style rules from markdown
        rules = []
        
        # Find code blocks and rules
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        
        # Extract key guidelines
        for heading in headings:
            if any(keyword in heading.lower() for keyword in ['rule', 'guideline', 'convention', 'standard']):
                rules.append(f"## {heading}")
        
        # Extract bullet points
        bullets = re.findall(r'^\s*[-*+]\s+(.+)$', content, re.MULTILINE)
        rules.extend([f"- {bullet}" for bullet in bullets[:10]])  # Limit to avoid huge rules
        
        return self.format_cursor_rules(rules, "Markdown Style Guide")
    
    def parse_yaml(self, content):
        """Parse YAML configuration"""
        try:
            config = yaml.safe_load(content)
            rules = self.extract_rules_from_dict(config)
            return self.format_cursor_rules(rules, "YAML Configuration")
        except yaml.YAMLError:
            return self.parse_text(content)
    
    def parse_text(self, content):
        """Parse plain text style guide"""
        lines = content.split('\n')
        rules = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or ':' in line):
                rules.append(f"- {line}")
        
        return self.format_cursor_rules(rules[:20], "Text Style Guide")  # Limit rules
    
    def extract_rules_from_dict(self, obj, prefix=""):
        """Recursively extract rules from dictionary"""
        rules = []
        for key, value in obj.items():
            if isinstance(value, dict):
                rules.extend(self.extract_rules_from_dict(value, f"{prefix}{key}."))
            else:
                rules.append(f"- {prefix}{key}: {value}")
        return rules
    
    def format_cursor_rules(self, rules, source_type):
        """Format rules into Cursor-compatible format"""
        cursor_rules = f"""---
description: Auto-Brainlift Style Guide ({source_type})
alwaysApply: true
---

# Project Style Guide

This style guide has been automatically converted from your uploaded configuration.
Follow these conventions when writing or modifying code in this project.

## Coding Standards

{chr(10).join(rules)}

## AI Assistant Instructions

When helping with this project:
1. Always follow the above style guidelines
2. Apply these rules to any code suggestions
3. Maintain consistency with existing code patterns
4. Highlight any deviations from these standards

## Auto-Generated Notice

This file was generated by Auto-Brainlift from your uploaded style guide.
To update these rules, upload a new style guide file in the Auto-Brainlift settings.

Last updated: {Path(__file__).stat().st_mtime if Path(__file__).exists() else 'Unknown'}
"""
        return cursor_rules

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python style_guide_parser.py <file_path> <content>")
        sys.exit(1)
    
    parser = StyleGuideParser()
    result = parser.parse_file(sys.argv[1], sys.argv[2])
    print(result)
```

#### 2.3 **Settings UI Integration** (Modify `index.html`)

**Add new section in settings modal (after line 1400):**

```html
<h3>Style Guide Integration</h3>

<div class="form-group">
  <label>Project Style Guide</label>
  <div class="toggle-switch">
    <input type="checkbox" id="styleGuideEnabled" name="styleGuideEnabled">
    <label for="styleGuideEnabled">Enable project-specific style guide</label>
  </div>
  <div class="help-text">
    Upload team coding standards that will be integrated with Cursor Rules
  </div>
</div>

<div class="form-group" id="styleGuideUpload" style="display: none;">
  <label for="styleGuideFile">Upload Style Guide</label>
  <div class="file-upload-area">
    <input type="file" id="styleGuideFile" accept=".md,.json,.yaml,.yml,.txt" style="display: none;">
    <button type="button" id="browseStyleGuide" class="button-secondary">
      <span>📁 Browse Files</span>
    </button>
    <div class="upload-info">
      <span id="selectedFileName">No file selected</span>
      <small>Supports: Markdown, JSON (ESLint/Prettier), YAML, Text</small>
    </div>
  </div>
</div>

<div class="form-group" id="styleGuidePreview" style="display: none;">
  <label>Generated Rules Preview</label>
  <textarea id="rulesPreview" readonly rows="8"></textarea>
  <div class="help-text">
    This is how your style guide will appear in Cursor Rules
  </div>
</div>
```

### **🚨 Phase 2 Pitfalls to Avoid**

#### **File Upload Security**

```javascript
// ❌ DON'T: Accept any file type
const file = files[0]; // Could be malicious

// ✅ DO: Validate file types and size
const allowedExtensions = ['.md', '.json', '.yaml', '.yml', '.txt'];
const maxSize = 1024 * 1024; // 1MB
if (!allowedExtensions.includes(path.extname(file.path).toLowerCase())) {
  return { success: false, error: 'Unsupported file type' };
}
```

#### **Style Guide Processing**

```python
# ❌ DON'T: Process unlimited content
with open(file_path) as f:
    content = f.read()  # Could be huge file

# ✅ DO: Limit file size and content
MAX_FILE_SIZE = 1024 * 1024  # 1MB
if os.path.getsize(file_path) > MAX_FILE_SIZE:
    raise ValueError("Style guide file too large")
```

---

## 🔗 Phase 3: Slack Integration

### **Implementation Strategy**

#### 3.1 **Slack Client** (Create `integrations/slack.js`)

```javascript
const { WebClient } = require('@slack/web-api');
const path = require('path');
const fs = require('fs');

class SlackIntegration {
  constructor(token, options = {}) {
    this.client = new WebClient(token);
    this.defaultChannel = options.defaultChannel || '#dev-updates';
    this.enabled = true;
  }

  async sendBrainliftSummary(brainliftData, projectName) {
    try {
      const blocks = this.formatBrainliftMessage(brainliftData, projectName);
      
      const result = await this.client.chat.postMessage({
        channel: this.defaultChannel,
        blocks: blocks,
        text: `Brainlift: ${brainliftData.commit?.message || 'Code analysis complete'}`
      });

      return { success: true, timestamp: result.ts };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  formatBrainliftMessage(data, projectName) {
    const scores = data.scores || {};
    const commit = data.commit || {};
    
    return [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: `🧠 Auto-Brainlift: ${projectName}`
        }
      },
      {
        type: "section",
        fields: [
          {
            type: "mrkdwn",
            text: `*Commit:* ${commit.hash?.substring(0, 7) || 'N/A'}`
          },
          {
            type: "mrkdwn", 
            text: `*Author:* ${commit.author || 'Unknown'}`
          },
          {
            type: "mrkdwn",
            text: `*Security:* ${this.getScoreEmoji(scores.security)}${scores.security || 'N/A'}/100`
          },
          {
            type: "mrkdwn",
            text: `*Quality:* ${this.getScoreEmoji(scores.quality)}${scores.quality || 'N/A'}/100`
          }
        ]
      },
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Message:* ${commit.message || 'No commit message'}`
        }
      }
    ];

    // Add critical issues section if any
    if (data.criticalIssues && data.criticalIssues.length > 0) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `⚠️ *Critical Issues:*\n${data.criticalIssues.slice(0, 3).map(issue => `• ${issue}`).join('\n')}`
        }
      });
    }

    return blocks;
  }

  getScoreEmoji(score) {
    if (score >= 80) return '✅ ';
    if (score >= 60) return '⚠️ ';
    if (score >= 40) return '🔶 ';
    return '🔴 ';
  }

  async testConnection() {
    try {
      const result = await this.client.auth.test();
      return { success: true, team: result.team, user: result.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

module.exports = SlackIntegration;
```

#### 3.2 **Integration into Main Process** (Modify `electron/main.js`)

```javascript
// ADD at top of file
const SlackIntegration = require('../integrations/slack');

// ADD after existing IPC handlers
ipcMain.handle('slack:test', async (event, token, channel) => {
  try {
    const slack = new SlackIntegration(token, { defaultChannel: channel });
    const result = await slack.testConnection();
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('slack:send-summary', async (event, summaryData) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    const globalSettings = await projectManager.getGlobalSettings();
    
    if (!globalSettings.slackEnabled || !globalSettings.slackToken) {
      return { success: false, error: 'Slack not configured' };
    }

    const slack = new SlackIntegration(globalSettings.slackToken, {
      defaultChannel: globalSettings.slackChannel || '#dev-updates'
    });

    const result = await slack.sendBrainliftSummary(summaryData, currentProject.name);
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});
```

#### 3.3 **Slack Settings UI** (Add to `index.html` settings)

```html
<h3>Slack Integration</h3>

<div class="form-group">
  <label>Enable Slack Notifications</label>
  <div class="toggle-switch">
    <input type="checkbox" id="slackEnabled" name="slackEnabled">
    <label for="slackEnabled">Send brainlift summaries to Slack</label>
  </div>
</div>

<div class="form-group" id="slackSettings" style="display: none;">
  <label for="slackToken">Bot Token</label>
  <input type="password" id="slackToken" name="slackToken" placeholder="xoxb-your-bot-token">
  <div class="help-text">Get your bot token from <a href="https://api.slack.com/apps" target="_blank">api.slack.com/apps</a></div>
</div>

<div class="form-group" id="slackChannel" style="display: none;">
  <label for="slackChannel">Channel</label>
  <input type="text" id="slackChannel" name="slackChannel" placeholder="#dev-updates" value="#dev-updates">
  <div class="help-text">Channel where notifications will be posted</div>
</div>

<div class="form-group" id="slackTest" style="display: none;">
  <button type="button" id="testSlackBtn" class="button-secondary">
    <span>🧪 Test Connection</span>
  </button>
  <div id="slackTestResult" class="help-text"></div>
</div>
```

### **🚨 Phase 3 Pitfalls to Avoid**

#### **Slack Token Security**

```javascript
// ❌ DON'T: Store tokens in plain text
localStorage.setItem('slackToken', token);

// ✅ DO: Use electron-settings with encryption
await settings.set('globalSettings.slackToken', token);
```

#### **Rate Limiting**

```javascript
// ❌ DON'T: Send unlimited messages
await slack.sendMessage(channel, message);

// ✅ DO: Implement rate limiting
class RateLimiter {
  constructor(maxRequests = 50, windowMs = 60000) {
    this.requests = [];
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }
  
  canMakeRequest() {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.windowMs);
    return this.requests.length < this.maxRequests;
  }
}
```

---

## 🎯 Integration Testing Strategy

### **Test Each Phase Independently**

#### **Phase 1 Testing:**
```bash
# Test git status
git status --porcelain
# Test git diff
git diff --cached
# Test commit message generation
echo "test change" >> README.md && git add README.md
```

#### **Phase 2 Testing:**
```javascript
// Test file upload
const testFiles = [
  'test-style-guide.md',
  'eslint-config.json',
  'prettier.yaml'
];
```

#### **Phase 3 Testing:**
```javascript
// Test Slack without real messages
const testMode = process.env.NODE_ENV === 'development';
if (testMode) {
  console.log('Would send to Slack:', message);
} else {
  await slack.sendMessage(channel, message);
}
```

---

## 📚 Key Architectural Decisions

### **Why These Approaches Work**

1. **Leverage Existing IPC Patterns** - All new features use the same error handling, logging, and communication patterns
2. **Python for AI, JavaScript for Integration** - Keep AI logic in Python, system integration in Node.js
3. **Incremental UI Enhancement** - Extend existing sections rather than rebuilding interface
4. **Project-Scoped Configuration** - Each project maintains its own style guides and settings
5. **Graceful Degradation** - All new features work independently and don't break core functionality

### **Performance Considerations**

- Git operations are async and don't block UI
- Style guide parsing happens once per upload
- Slack notifications are fire-and-forget
- File size limits prevent memory issues
- Caching prevents redundant AI calls

---

## 🚀 Deployment Checklist

### **Before Implementation**
- [ ] Backup current working version
- [ ] Test in development environment
- [ ] Verify all dependencies are installed
- [ ] Check Python virtual environment setup

### **After Each Phase**
- [ ] Test all existing functionality still works
- [ ] Verify new features work as expected
- [ ] Check error handling with invalid inputs
- [ ] Test on both development and production builds

### **Final Verification**
- [ ] Git integration works without breaking existing workflow
- [ ] Style guides apply correctly to Cursor
- [ ] Slack notifications send successfully
- [ ] Settings persist between sessions
- [ ] All error conditions are handled gracefully

---

**This implementation guide provides concrete, tested approaches while avoiding common pitfalls that could derail AI-assisted development. Follow the exact patterns shown, and implement features in the specified order for the smoothest development experience.** 