# Auto-Brainlift v2.0 Implementation Checklist
## Systematic Development Guide

---

## 📋 PRE-IMPLEMENTATION VERIFICATION

### **Environment Readiness**
- [ ] Current Auto-Brainlift working: `npm start` launches successfully
- [ ] Python virtual environment active: `venv/bin/python3` available
- [ ] Existing brainlift generation working (test with Generate Summary)
- [ ] Git repository initialized and working
- [ ] OpenAI API key configured and functional
- [ ] Development branch created: `git checkout -b feature/v2-implementation`

### **Dependencies Verified**
- [ ] Node.js dependencies: `npm install` completed without errors
- [ ] Python dependencies: `pip install -r requirements.txt` successful
- [ ] Git CLI available: `git --version` returns valid version
- [ ] Virtual environment isolated: `which python3` points to venv

---

## 🚀 PHASE 1: GIT WORKFLOW FOUNDATION

### **Step 1.1: Git Status Backend (45 minutes)**
**File:** `auto-brainlift/electron/main.js`
**Location:** After line 602

**Implementation:**
- [ ] Add git status IPC handler with project validation
- [ ] Parse git status --porcelain output
- [ ] Return structured response with staged/unstaged counts

**Test Criteria:**
- [ ] Handler returns success response with git data when in git repo
- [ ] Returns error when not in git repo
- [ ] Correctly identifies staged vs unstaged files
- [ ] Test with DevTools: `window.electronAPI.git.status()`

### **Step 1.2: Git Operations Backend (30 minutes)**
**File:** `auto-brainlift/electron/main.js`
**Location:** After git:status handler

- [ ] Add git commit handler:
```javascript
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
```

- [ ] Add git push/pull handlers (similar pattern)

**Test Criteria:**
- [ ] Commit handler executes git command properly
- [ ] Error handling for failed commits
- [ ] Operations run in correct project directory

### **Step 1.3: AI Commit Message Generator (60 minutes)**
**File:** `auto-brainlift/agents/commit_message_generator.py`

**Implementation:**
- [ ] Create Python script using LangChain OpenAI
- [ ] Accept git diff via environment variable
- [ ] Generate conventional commit format messages
- [ ] Handle errors gracefully

**Test Criteria:**
- [ ] Script executes without errors when run standalone
- [ ] Generates sensible commit messages from git diff
- [ ] Handles missing API key gracefully
- [ ] Outputs clean message format

### **Step 1.4: Commit Message IPC Handler (30 minutes)**
**File:** `auto-brainlift/electron/main.js`
**Location:** After git operations handlers

- [ ] Add commit message generation handler:
```javascript
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

**Test Criteria:**
- [ ] Handler gets git diff for staged changes
- [ ] Spawns Python script with correct environment
- [ ] Returns generated commit message
- [ ] Handles errors from Python script

### **Step 1.5: Preload API Extension (15 minutes)**
**File:** `auto-brainlift/electron/preload.js`
**Location:** After line 92

- [ ] Add Git API to electronAPI:
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

**Test Criteria:**
- [ ] All git APIs available in renderer: `window.electronAPI.git`
- [ ] Status API callable: `window.electronAPI.git.status()`
- [ ] Commit message API callable: `window.electronAPI.git.generateCommitMessage()`

### **Step 1.6: UI Integration - HTML Structure (45 minutes)**
**File:** `auto-brainlift/index.html`
**Location:** Replace Manual Generation section at line 1134

**Implementation:**
- [ ] Expand Manual Generation section with git controls
- [ ] Add git status display and buttons
- [ ] Add commit message container with actions
- [ ] Add CSS styling for new elements
- [ ] Add JavaScript event handlers

**Test Criteria:**
- [ ] Manual Generation section updated with git controls
- [ ] All buttons and containers present
- [ ] Layout maintains existing design consistency

### **Step 1.7: UI Integration - CSS Styling (30 minutes)**
**File:** `auto-brainlift/index.html`
**Location:** After line 400 in CSS section

- [ ] Add Git controls styling:
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

**Test Criteria:**
- [ ] Git controls styled consistently with existing theme
- [ ] Status display visible and properly formatted
- [ ] Commit message container hidden by default
- [ ] Buttons follow existing design patterns

### **Step 1.8: UI Integration - JavaScript Logic (60 minutes)**
**File:** `auto-brainlift/index.html`
**Location:** After line 1600 in script section

- [ ] Add Git controls JavaScript:
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

**Test Criteria:**
- [ ] Git status updates automatically
- [ ] Commit button disabled when no staged changes
- [ ] Commit message generation works
- [ ] Commit workflow completes successfully
- [ ] UI updates after operations

---

## 🧪 PHASE 1 TESTING & VALIDATION

### **Comprehensive Testing (30 minutes)**
- [ ] Load test file: Copy `test_git_integration_v2.js` into DevTools console
- [ ] Run full test suite: `window.gitTests.runAll()`
- [ ] Verify all test criteria pass:
  - [ ] Git status API working
  - [ ] Commit message generation working
  - [ ] Git operations working
  - [ ] UI integration working
  - [ ] Error handling working

### **Manual Validation (15 minutes)**
- [ ] Create test changes: `echo "test" >> README.md`
- [ ] Stage changes: `git add README.md`
- [ ] Test git status in UI shows staged changes
- [ ] Generate commit message and verify quality
- [ ] Complete commit workflow and verify git log
- [ ] Test with no changes (buttons should be disabled)

### **Phase 1 Sign-off**
- [ ] All automated tests passing
- [ ] Manual validation complete
- [ ] No existing functionality broken
- [ ] Git integration fully functional
- [ ] Ready to proceed to Phase 2

---

## 🎨 PHASE 2: STYLE GUIDE INTEGRATION

### **Step 2.1: Style Guide Settings UI (45 minutes)**
**File:** `auto-brainlift/index.html`
**Location:** In settings modal after Cursor Rules Integration section

- [ ] Add Style Guide Integration section to settings:
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

**Test Criteria:**
- [ ] Style Guide section appears in settings modal
- [ ] Toggle switch shows/hides upload controls
- [ ] File input accepts specified formats only
- [ ] Browse button triggers file dialog

---

## ⚡ CONTINUING WITH SYSTEMATIC IMPLEMENTATION...

*This checklist continues with Step 2.2 through Phase 3 completion. Each step includes:*
- **Specific file locations and line numbers**
- **Complete code implementations**
- **Test criteria for validation**
- **Time estimates for planning**

---

## 📊 PROGRESS TRACKING

### **Phase 1: Git Workflow** [3 steps, ~3 hours]
- [ ] 1.1 Git Status Backend (45 min)
- [ ] 1.2 AI Commit Message Generator (60 min)
- [ ] 1.3 UI Integration (60 min)

### **Phase 2: Style Guide** [Coming Next]
- [ ] File upload and parsing system
- [ ] Cursor Rules generation
- [ ] Project-specific isolation

### **Phase 3: Slack Integration** [Coming Next]
- [ ] Slack API client integration
- [ ] Message formatting and templates
- [ ] Notification workflows

---

## 🎯 SUCCESS CRITERIA

**Phase 1 Complete When:**
- [ ] Git status shows in UI with live updates
- [ ] AI-generated commit messages work
- [ ] Commit/push/pull buttons functional
- [ ] All existing features still work perfectly

**Phase 2 Complete When:**
- [ ] Style guides upload and parse correctly
- [ ] Cursor rules integrate properly
- [ ] Project isolation maintained

**Phase 3 Complete When:**
- [ ] Slack notifications send after brainlifts
- [ ] Settings UI complete and functional
- [ ] Error handling robust

**Final Release Ready When:**
- [ ] All test suites passing
- [ ] Manual validation complete
- [ ] Documentation updated
- [ ] No regressions in existing functionality 