# CURSOR AI KICKOFF PROMPT
## Auto-Brainlift v2.0 Implementation

---

## 🎯 Project Context

You are implementing **Auto-Brainlift v2.0** - adding advanced workflow automation to an existing, working Electron + Python application. This is NOT a greenfield project - you're extending a mature codebase with specific patterns and architecture.

**Current State:** Auto-Brainlift v1.0 is a fully functional desktop app that generates AI-powered Git commit summaries using a multi-agent system (Security, Quality, Documentation agents) with LangChain and OpenAI integration.

**Your Mission:** Add 3 new feature sets while maintaining 100% backward compatibility:
1. **Git Workflow Controls** - AI commit messages, commit/push/pull buttons
2. **Style Guide Integration** - Upload team coding standards, convert to Cursor Rules
3. **Slack Integration** - Automated notifications for brainlift summaries

---

## 📚 CRITICAL: Read These Documents First

**PRIMARY CHECKLIST:** `CURSOR_AI_CHECKLIST.md`
- Your step-by-step implementation guide
- Each checkbox = 30-60 minutes of focused work
- NEVER skip steps or work out of order

**IMPLEMENTATION PATTERNS:** `AI_IMPLEMENTATION_SUMMARY.md`
- Exact code patterns to follow
- Research-based best practices
- Critical pitfalls to avoid

**ARCHITECTURE GUIDE:** `FEATURE_ROADMAP_v2.md`
- Complete feature specifications
- Technical architecture decisions

---

## 🏗️ Architecture You Must Understand

### **Existing Patterns (FOLLOW THESE EXACTLY):**

**IPC Communication Pattern:**
```javascript
// In electron/main.js - COPY THIS PATTERN
ipcMain.handle('action-name', async (event, data) => {
  try {
    const currentProject = projectManager.getCurrentProject();
    if (!currentProject) {
      return { success: false, error: 'No project selected' };
    }
    // ... implementation
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});
```

**Python Process Spawning Pattern:**
```javascript
// COPY THIS PATTERN from existing code
const pythonProcess = spawn(pythonCommand, args, {
  cwd: currentProject.path,
  env: { 
    ...process.env,
    PYTHONPATH: path.join(__dirname, '..'),
    OPENAI_API_KEY: globalSettings.apiKey || ''
  }
});
```

**Settings Management Pattern:**
```javascript
// In projectManager.js - EXTEND THIS STRUCTURE
this.projects[projectId].settings = {
  // existing settings...
  // ADD YOUR NEW SETTINGS HERE
};
```

### **File Locations (EXACT LINES SPECIFIED):**
- `electron/main.js` - Add IPC handlers after line 602
- `electron/preload.js` - Add API exports after line 92
- `index.html` - Replace Manual Generation section at line 1134
- `index.html` - Add CSS after line 400
- `index.html` - Add JavaScript after line 1600

---

## 🚀 START HERE: Phase 1, Step 1

**IMMEDIATE TASK:** Implement Git Status API

**File:** `electron/main.js`
**Location:** After line 602
**Time Estimate:** 45 minutes

**Implementation:**
1. Add the git status IPC handler using the existing pattern
2. Use `spawn('git', ['status', '--porcelain'])` with proper error handling
3. Parse the output to identify staged vs unstaged files
4. Return success/error response matching existing patterns
5. Test with DevTools: `window.electronAPI.git.status()`

**Code Template:**
```javascript
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
    logToFile(`Git status error: ${error.message}`);
    return { success: false, error: error.message };
  }
});
```

**Test Criteria:**
- [ ] Handler added to main.js after line 602
- [ ] Returns success response with git data when in git repo
- [ ] Returns error when not in git repo
- [ ] Correctly identifies staged vs unstaged files
- [ ] Test with: `window.electronAPI.git.status()` in DevTools console

---

## 🚨 CRITICAL DEVELOPMENT RULES

### **DO:**
- Follow the EXACT patterns shown in existing code
- Test each step before proceeding to the next
- Use the checklist sequentially - each checkbox represents one focused task
- Reference the implementation guides when stuck
- Maintain the existing error handling patterns
- Use the same logging pattern with `logToFile()`

### **DON'T:**
- Modify existing core functionality unless explicitly required
- Skip steps in the checklist
- Invent new patterns when existing ones work
- Add dependencies not listed in the guides
- Break existing functionality
- Work on multiple phases simultaneously

### **IF YOU GET STUCK:**
1. Re-read the relevant section in `AI_IMPLEMENTATION_SUMMARY.md`
2. Look at similar existing code patterns in the codebase
3. Check the `CURSOR_AI_CHECKLIST.md` for the exact next step
4. Ask for clarification rather than guessing

### **RED FLAGS (STOP IMMEDIATELY):**
- You're modifying `langgraph_agent.py` or core agent files
- You're changing the database schema
- You're adding new Python dependencies
- You're restructuring existing file organization
- You're getting import errors from Python scripts

---

## 🧪 Testing Protocol

**After Each Implementation Step:**
1. Test the specific functionality you just added
2. Verify existing features still work (run `npm start` and test brainlift generation)
3. Check the console for any new errors
4. Commit working code with descriptive messages

**Key Test Commands:**
```bash
# Test current app works
npm start

# Test Python environment
venv/bin/python3 agents/langgraph_agent.py

# Test git functionality (when implemented)
# In DevTools console:
window.electronAPI.git.status()
```

---

## 🎯 Success Metrics

**Phase 1 Complete When:**
- Git status shows in UI with live updates
- AI-generated commit messages work
- Commit/push/pull buttons functional
- All existing features still work perfectly

**Phase 2 Complete When:**
- Style guides upload and parse correctly
- Cursor rules integrate properly
- Project isolation maintained

**Phase 3 Complete When:**
- Slack notifications send after brainlifts
- Settings UI complete and functional
- Error handling robust

---

## 📁 Key Files You'll Work With

**Modify These:**
- `electron/main.js` (IPC handlers)
- `electron/preload.js` (API exports)
- `index.html` (UI and styling)
- `electron/projectManager.js` (settings)

**Create These:**
- `agents/commit_message_generator.py`
- `agents/style_guide_parser.py`
- `integrations/slack.js`

**Never Touch:**
- `agents/langgraph_agent.py` (core brainlift logic)
- `agents/base_agent.py` (agent framework)
- `package.json` (until Phase 3 Slack dependency)

---

## 🔄 Development Flow

1. **Read the checklist item completely**
2. **Understand the specific task and test criteria**
3. **Implement using existing patterns**
4. **Test immediately**
5. **Check off the item**
6. **Move to next item**

**Time Allocation:**
- Phase 1: 2-3 weeks (Git controls)
- Phase 2: 3-4 weeks (Style guides)  
- Phase 3: 2-3 weeks (Slack integration)

---

## 💬 Communication Protocol

**When reporting progress:**
- Specify which checklist item you completed
- Mention any deviations from the plan
- Note any issues discovered
- Confirm test criteria were met

**When asking for help:**
- Reference the specific checklist step
- Describe what you've tried
- Share any error messages
- Specify which guide you consulted

---

**BEGIN WITH:** Phase 1, Step 1.1 - Backend Git Status API (shown above)

**REMEMBER:** This is extending a working system, not building from scratch. Follow the patterns, test incrementally, and maintain backward compatibility at all costs.

You have everything you need in the documentation. Start with the git status implementation and work through the checklist systematically. Good luck! 