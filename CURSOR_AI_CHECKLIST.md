# Auto-Brainlift v2.0 Implementation Checklist
## Cursor AI Step-by-Step Development Guide

---

## 🎯 Purpose
This checklist prevents AI from wandering off-track during development. Complete each task in sequence, checking off items as you go.

---

## 📋 Pre-Implementation Setup

### **Environment Verification**
- [ ] Confirm current Auto-Brainlift is working (run `npm start`)
- [ ] Verify Python virtual environment is active (`venv/bin/python3`)
- [ ] Test existing brainlift generation works
- [ ] Backup current working version
- [ ] Create development branch: `git checkout -b feature/v2-implementation`

### **Dependencies Check**
- [ ] Node.js modules installed (`npm install`)
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] OpenAI API key configured and working
- [ ] Git is available in system PATH

---

## 🚀 Phase 1: Git Workflow Foundation

### **Step 1.1: Backend Git Status API**
**File:** `electron/main.js`
**Location:** After line 602

- [ ] Add git status IPC handler:
```javascript
ipcMain.handle('git:status', async (event) => {
  // Implementation from AI_IMPLEMENTATION_SUMMARY.md
});
```

**Test Criteria:**
- [ ] Handler returns success/error response
- [ ] Correctly identifies staged vs unstaged files
- [ ] Handles non-git directories gracefully
- [ ] Test with: `window.electronAPI.git.status()` in DevTools

### **Step 1.2: Backend Git Operations**
**File:** `electron/main.js`
**Location:** After git:status handler

- [ ] Add commit handler:
```javascript
ipcMain.handle('git:commit', async (event, message) => {
  // Implementation from guide
});
```

- [ ] Add push handler:
```javascript
ipcMain.handle('git:push', async (event) => {
  // Similar pattern to commit
});
```

- [ ] Add pull handler:
```javascript
ipcMain.handle('git:pull', async (event) => {
  // Similar pattern to commit
});
```

**Test Criteria:**
- [ ] Each handler has proper error handling
- [ ] Operations run in correct project directory
- [ ] Success/error responses are consistent
- [ ] Test manually: stage file, commit, verify in git log

### **Step 1.3: AI Commit Message Generator**
**File:** `agents/commit_message_generator.py` (NEW FILE)

- [ ] Create new Python file with shebang
- [ ] Add sys.path.insert for imports
- [ ] Implement generate_commit_message() function
- [ ] Use existing LangChain pattern from project
- [ ] Handle environment variables (OPENAI_API_KEY, GIT_DIFF)
- [ ] Use gpt-4o-mini model (cost-effective)
- [ ] Temperature 0.3 for consistency

**Test Criteria:**
- [ ] Script runs without errors: `python3 agents/commit_message_generator.py`
- [ ] Generates reasonable commit messages
- [ ] Handles empty diff gracefully
- [ ] Returns clean output (no extra whitespace/quotes)

### **Step 1.4: Backend AI Integration**
**File:** `electron/main.js`
**Location:** After git operations handlers

- [ ] Add AI commit message handler:
```javascript
ipcMain.handle('git:generate-commit-message', async (event) => {
  // Get git diff, spawn Python script, return message
});
```

**Test Criteria:**
- [ ] Gets git diff for staged changes only
- [ ] Passes diff to Python script via environment
- [ ] Returns AI-generated message
- [ ] Handles Python script failures gracefully

### **Step 1.5: Frontend API Extension**
**File:** `electron/preload.js`
**Location:** After line 92

- [ ] Add git API to electronAPI:
```javascript
git: {
  status: () => ipcRenderer.invoke('git:status'),
  generateCommitMessage: () => ipcRenderer.invoke('git:generate-commit-message'),
  commit: (message) => ipcRenderer.invoke('git:commit', message),
  push: () => ipcRenderer.invoke('git:push'),
  pull: () => ipcRenderer.invoke('git:pull')
}
```

**Test Criteria:**
- [ ] API accessible in renderer: `window.electronAPI.git`
- [ ] Each method returns Promise
- [ ] Test in DevTools console

### **Step 1.6: UI Controls HTML**
**File:** `index.html`
**Location:** Replace Manual Generation section (line 1134)

- [ ] Replace existing section with expanded version:
  - [ ] Keep original "Generate Summary" button
  - [ ] Add "Analyze WIP" button
  - [ ] Add git status display area
  - [ ] Add commit/push/pull buttons
  - [ ] Add commit message container (hidden by default)
  - [ ] Add commit message textarea
  - [ ] Add accept/edit/cancel buttons

**Test Criteria:**
- [ ] All buttons render correctly
- [ ] Layout doesn't break existing design
- [ ] Commit message container starts hidden
- [ ] Buttons have proper IDs for JavaScript

### **Step 1.7: UI Controls CSS**
**File:** `index.html`
**Location:** After line 400 in style section

- [ ] Add CSS classes:
  - [ ] `.controls-group` - Flex layout for button groups
  - [ ] `.git-status` - Status display styling
  - [ ] `.git-controls` - Button container
  - [ ] `#commitMessageContainer` - Modal-style container
  - [ ] `#commitMessageText` - Textarea styling
  - [ ] `.commit-actions` - Button group for commit actions

**Test Criteria:**
- [ ] Styling matches existing design system
- [ ] Uses existing CSS variables (--spacing-md, --color-border, etc.)
- [ ] Responsive layout doesn't break on smaller screens
- [ ] Colors match existing theme

### **Step 1.8: UI Controls JavaScript**
**File:** `index.html`
**Location:** After line 1600 in script section

- [ ] Add element references for all new buttons
- [ ] Implement `updateGitStatus()` function
- [ ] Add event listeners:
  - [ ] commitBtn click - generate commit message
  - [ ] acceptCommitBtn click - perform commit
  - [ ] pushBtn click - git push
  - [ ] pullBtn click - git pull
  - [ ] editCommitBtn click - enable editing
  - [ ] cancelCommitBtn click - hide container

- [ ] Add status update interval (every 10 seconds)

**Test Criteria:**
- [ ] Git status updates automatically
- [ ] Commit button disabled when no staged changes
- [ ] Commit message generation works and shows in textarea
- [ ] Accept commit actually commits and updates status
- [ ] Error handling shows user-friendly messages

### **Phase 1 Testing Checklist**
- [ ] Stage a file: `git add README.md`
- [ ] Git status shows staged changes in UI
- [ ] Commit button becomes enabled
- [ ] Click commit button generates AI message
- [ ] Edit message in textarea works
- [ ] Accept commit creates actual git commit
- [ ] Git status updates to show clean state
- [ ] Push button works (if remote configured)
- [ ] Error handling: test in non-git directory

---

## 🎨 Phase 2: Style Guide System

### **Step 2.1: Directory Structure**
- [ ] Create `integrations/` directory
- [ ] Create `.auto-brainlift/style-guide/` in project directory (via code)

### **Step 2.2: Style Guide Parser**
**File:** `agents/style_guide_parser.py` (NEW FILE)

- [ ] Create StyleGuideParser class
- [ ] Implement methods:
  - [ ] `parse_json()` - Handle ESLint, Prettier configs
  - [ ] `parse_yaml()` - Handle YAML configurations  
  - [ ] `parse_markdown()` - Extract rules from markdown
  - [ ] `parse_text()` - Handle plain text files
  - [ ] `format_cursor_rules()` - Convert to Cursor format

**Test Criteria:**
- [ ] Parses sample ESLint config correctly
- [ ] Generates valid Cursor rules format
- [ ] Handles invalid files gracefully
- [ ] Script executable: `python3 agents/style_guide_parser.py test.json`

### **Step 2.3: File Upload Backend**
**File:** `electron/main.js`
**Location:** After existing IPC handlers

- [ ] Add file upload handler:
```javascript
ipcMain.handle('style-guide:upload', async (event, filePath) => {
  // Validate file, copy to project, parse, save rules
});
```

- [ ] File validation:
  - [ ] Check allowed extensions (.md, .json, .yaml, .yml, .txt)
  - [ ] Check file size limit (1MB)
  - [ ] Verify file exists

- [ ] Processing:
  - [ ] Copy file to `.auto-brainlift/style-guide/`
  - [ ] Call Python parser script
  - [ ] Save generated rules to cursor-rules.md
  - [ ] Update project settings

**Test Criteria:**
- [ ] Rejects invalid file types
- [ ] Rejects oversized files
- [ ] Successfully processes valid style guides
- [ ] Updates project settings correctly

### **Step 2.4: Settings UI Extension**
**File:** `index.html`
**Location:** In settings modal, after Cursor Rules section

- [ ] Add "Style Guide Integration" section:
  - [ ] Enable toggle checkbox
  - [ ] File upload area (hidden when disabled)
  - [ ] Browse button
  - [ ] File info display
  - [ ] Rules preview textarea (hidden initially)

**Test Criteria:**
- [ ] Section integrates with existing settings modal
- [ ] Toggle shows/hides upload area
- [ ] File picker opens with correct filters
- [ ] Preview area shows generated rules

### **Step 2.5: Settings JavaScript Integration**
**File:** `index.html`
**Location:** In settings JavaScript section

- [ ] Add event listeners:
  - [ ] Style guide toggle change
  - [ ] Browse button click
  - [ ] File selection change
  - [ ] Upload and preview functionality

- [ ] Add functions:
  - [ ] `handleStyleGuideUpload()`
  - [ ] `previewStyleGuide()`
  - [ ] `toggleStyleGuideSection()`

**Test Criteria:**
- [ ] Upload triggers file processing
- [ ] Preview shows parsed rules
- [ ] Settings save/load correctly
- [ ] Error states handled gracefully

### **Phase 2 Testing Checklist**
- [ ] Upload ESLint config file
- [ ] Verify rules preview shows correct format
- [ ] Check `.auto-brainlift/style-guide/` directory created
- [ ] Verify cursor-rules.md file generated
- [ ] Test with different file formats (JSON, YAML, Markdown)
- [ ] Verify project settings updated
- [ ] Test error cases (invalid files, large files)

---

## 🔗 Phase 3: Slack Integration

### **Step 3.1: Slack Client Module**
**File:** `integrations/slack.js` (NEW FILE)

- [ ] Install dependency: `npm install @slack/web-api`
- [ ] Create SlackIntegration class
- [ ] Implement methods:
  - [ ] `constructor(token, options)`
  - [ ] `sendBrainliftSummary(data, projectName)`
  - [ ] `formatBrainliftMessage(data, projectName)`
  - [ ] `getScoreEmoji(score)`
  - [ ] `testConnection()`

**Test Criteria:**
- [ ] Class instantiates without errors
- [ ] Test connection works with valid token
- [ ] Message formatting creates valid Slack blocks
- [ ] Handles API errors gracefully

### **Step 3.2: Slack Backend Integration**
**File:** `electron/main.js`
**Location:** After existing IPC handlers

- [ ] Add Slack integration handlers:
```javascript
ipcMain.handle('slack:test', async (event, token, channel) => {
  // Test Slack connection
});

ipcMain.handle('slack:send-summary', async (event, summaryData) => {
  // Send brainlift summary to Slack
});
```

**Test Criteria:**
- [ ] Test handler validates token and returns connection info
- [ ] Send handler formats and sends message correctly
- [ ] Error handling for invalid tokens/channels
- [ ] Rate limiting considerations

### **Step 3.3: Settings UI for Slack**
**File:** `index.html`
**Location:** In settings modal, after Style Guide section

- [ ] Add "Slack Integration" section:
  - [ ] Enable toggle
  - [ ] Bot token input (password type)
  - [ ] Channel input with default #dev-updates
  - [ ] Test connection button
  - [ ] Notification rules selector
  - [ ] Test result display area

**Test Criteria:**
- [ ] Section follows existing settings patterns
- [ ] Token input is password-masked
- [ ] Test button shows connection status
- [ ] Settings persist between sessions

### **Step 3.4: Brainlift Integration**
**File:** Find where brainlifts are generated and completed
**Location:** Likely in Python completion handler

- [ ] Identify where brainlift generation completes
- [ ] Add Slack notification trigger:
```javascript
// After successful brainlift generation
if (globalSettings.slackEnabled) {
  const slackData = {
    scores: results.overall_scores,
    commit: results.commit_info,
    criticalIssues: results.critical_issues
  };
  await electronAPI.slack.sendSummary(slackData);
}
```

**Test Criteria:**
- [ ] Notifications sent after successful brainlift
- [ ] No notifications when Slack disabled
- [ ] Handles Slack failures without breaking brainlift
- [ ] Respects notification rules (all/issues/critical)

### **Step 3.5: Settings JavaScript**
**File:** `index.html`
**Location:** In settings JavaScript section

- [ ] Add Slack settings handling:
  - [ ] Toggle enable/disable
  - [ ] Token validation
  - [ ] Test connection functionality
  - [ ] Save/load settings

**Test Criteria:**
- [ ] Settings save correctly
- [ ] Test connection shows results
- [ ] Token field behavior correct
- [ ] Integration with existing settings system

### **Phase 3 Testing Checklist**
- [ ] Create Slack app and get bot token
- [ ] Add bot to test channel
- [ ] Test connection in settings
- [ ] Generate brainlift and verify Slack message
- [ ] Test different notification rules
- [ ] Verify error handling (invalid token, offline)
- [ ] Test rate limiting doesn't break app

---

## 🧪 Final Integration Testing

### **Cross-Feature Testing**
- [ ] Git workflow works with style guides enabled
- [ ] Slack notifications include style guide compliance info
- [ ] All features work independently
- [ ] Disabling features doesn't break others

### **Error Scenarios**
- [ ] Non-git directory handling
- [ ] Network offline scenarios
- [ ] Invalid API keys
- [ ] Corrupted style guide files
- [ ] Slack API failures

### **Performance Testing**
- [ ] Large git diffs don't timeout
- [ ] Style guide parsing reasonable for large files
- [ ] UI remains responsive during operations
- [ ] Memory usage acceptable

### **User Experience Testing**
- [ ] All buttons provide feedback
- [ ] Error messages are user-friendly
- [ ] Loading states clear
- [ ] Settings persist correctly
- [ ] Help text is accurate

---

## 📚 Completion Criteria

### **Phase 1 Complete When:**
- [ ] All git operations work reliably
- [ ] AI commit messages generate correctly
- [ ] UI integrated and functional
- [ ] No regression in existing features

### **Phase 2 Complete When:**
- [ ] Style guides upload and parse correctly
- [ ] Cursor rules integrate properly
- [ ] Multiple file formats supported
- [ ] Project isolation maintained

### **Phase 3 Complete When:**
- [ ] Slack notifications send reliably
- [ ] Integration with brainlift flow works
- [ ] Settings UI complete and functional
- [ ] Error handling robust

### **Project Complete When:**
- [ ] All features work together harmoniously
- [ ] Documentation updated
- [ ] No breaking changes to existing functionality
- [ ] Ready for version release

---

## 🚨 AI Development Guardrails

### **If You Get Stuck:**
1. **Check the implementation guides first** - Don't invent new patterns
2. **Follow existing code patterns** - Look at how similar features are implemented
3. **Test incrementally** - Don't build everything before testing
4. **Maintain backward compatibility** - New features should be optional

### **Red Flags (Stop and Reconsider):**
- Modifying existing core functionality without clear need
- Adding dependencies not listed in the guides
- Creating new architectures instead of extending existing ones
- Breaking existing tests or functionality

### **Success Patterns:**
- Each checkbox represents 30-60 minutes of focused work
- Test each step before proceeding to next
- Commit working code frequently
- Follow the error handling patterns from existing code

---

**This checklist ensures systematic, step-by-step implementation without losing focus. Complete each section fully before moving to the next.** 