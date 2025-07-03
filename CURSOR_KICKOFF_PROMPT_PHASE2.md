# CURSOR AI KICKOFF PROMPT - PHASE 2
## Auto-Brainlift v2.0 Style Guide Integration

---

## 🎯 Project Status & Context

**Phase 1 Status:** ✅ **COMPLETED SUCCESSFULLY** (July 2, 2025)
- Commit: `0b40378` - "feat(git): implement AI commit message generation and controls"  
- All git workflow features working in production
- AI commit message generation with GPT-4o-mini functioning perfectly
- 100% backward compatibility maintained

**Current Mission:** Implement **Phase 2: Style Guide Integration** - Upload team coding standards and convert to Cursor Rules with project-specific isolation.

---

## 📚 CRITICAL: Reference These Foundation Documents

**PRIMARY IMPLEMENTATION GUIDE:** `IMPLEMENTATION_GUIDE_v2.md`
- Complete technical specifications for Phase 2
- Exact code patterns to follow
- File upload security and validation

**ARCHITECTURAL REFERENCE:** `CURSOR_IMPLEMENTATION_GUIDE.md`
- Style guide parser implementation details
- Project isolation strategy
- Cursor Rules integration patterns

**FEATURE SPECIFICATIONS:** `FEATURE_ROADMAP_v2.md`
- Complete Phase 2 feature requirements
- UI/UX integration points
- Success metrics and testing criteria

**STEP-BY-STEP CHECKLIST:** `CURSOR_AI_CHECKLIST.md`
- Phase 2 implementation steps (currently unchecked)
- Exact file locations and code additions
- Testing criteria for each component

---

## 🏗️ Phase 2 Architecture Overview

### **What You're Building:**

**1. Style Guide Upload System**
- File upload handler with security validation
- Support for multiple formats: Markdown, JSON (ESLint/Prettier), YAML, Text
- File size limits (1MB) and type validation
- Project-specific storage in `.auto-brainlift/style-guide/`

**2. Multi-Format Parser** 
- Python script: `agents/style_guide_parser.py`
- JSON parser for ESLint/Prettier configurations
- YAML parser for team configurations  
- Markdown parser extracting coding guidelines
- Text parser for plain style guides

**3. Cursor Rules Integration**
- Convert all formats to unified Cursor Rules format
- Project-specific isolation (no cross-contamination)
- Preview functionality before applying
- Automatic `.cursor/rules/` integration

**4. Settings UI Extension**
- New "Style Guide Integration" section in settings modal
- File upload interface with drag-and-drop
- Rules preview panel
- Enable/disable toggle per project

---

## 🚀 START HERE: Phase 2, Step 2.1

**IMMEDIATE TASK:** Implement Style Guide Upload Handler

**File:** `electron/main.js`
**Location:** After existing IPC handlers (around line 800)
**Time Estimate:** 60 minutes

**Implementation Pattern:**
```javascript
// ADD after existing IPC handlers
ipcMain.handle('style-guide:upload', async (event, filePath) => {
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
      return { success: false, error: 'Unsupported file type' };
    }
    
    if (stats.size > maxSize) {
      return { success: false, error: 'File too large (max 1MB)' };
    }

    // Create project style guide directory
    const styleGuideDir = path.join(currentProject.path, '.auto-brainlift', 'style-guide');
    if (!fs.existsSync(styleGuideDir)) {
      fs.mkdirSync(styleGuideDir, { recursive: true });
    }
    
    // Copy file to project
    const fileName = path.basename(filePath);
    const targetPath = path.join(styleGuideDir, fileName);
    fs.copyFileSync(filePath, targetPath);
    
    // Read file content for parsing
    const content = fs.readFileSync(filePath, 'utf8');
    
    return { 
      success: true, 
      fileName: fileName,
      targetPath: targetPath,
      content: content.substring(0, 500) + '...' // Preview
    };
    
  } catch (error) {
    logToFile(`Style guide upload error: ${error.message}`);
    return { success: false, error: error.message };
  }
});
```

**Test Criteria:**
- [ ] Handler accepts valid file types (.md, .json, .yaml, .txt)
- [ ] Rejects invalid file types and oversized files
- [ ] Creates `.auto-brainlift/style-guide/` directory
- [ ] Copies file to project directory successfully
- [ ] Returns file preview for UI display
- [ ] Test with: `window.electronAPI.styleGuide.upload()` in DevTools

---

## 🚨 CRITICAL SUCCESS PATTERNS

### **Follow Phase 1 Patterns Exactly:**
- **IPC Handler Structure:** Use same try/catch and success/error response format
- **Project Validation:** Always check `projectManager.getCurrentProject()`
- **Error Logging:** Use `logToFile()` for all errors
- **File Operations:** Create directories with `{ recursive: true }`

### **Security First:**
- **File Type Validation:** Never trust file extensions alone
- **Size Limits:** Enforce 1MB maximum to prevent memory issues  
- **Path Sanitization:** Use `path.basename()` to prevent directory traversal
- **Content Validation:** Basic content checks before processing

### **Project Isolation:**
- **Separate Directories:** Each project gets own `.auto-brainlift/style-guide/`
- **No Global State:** Style guides don't affect other projects
- **Clean Separation:** Cursor rules generated per-project only

---

## 🧪 Testing Protocol

**After Each Step:**
1. Test the specific functionality you just added
2. Verify no regression in Phase 1 git features  
3. Check error handling with invalid inputs
4. Test file operations don't break on different OS

**Phase 2 Success Metrics:**
- Upload various style guide formats successfully
- Generate valid Cursor rules from each format  
- Preview shows correctly formatted rules
- Projects remain isolated from each other
- All existing features continue working

---

## 🎯 Phase 2 Completion Goals

**When Phase 2 is Complete:**
- [ ] Teams can upload existing ESLint/Prettier configs
- [ ] Markdown style guides convert to Cursor rules
- [ ] YAML team standards integrate seamlessly
- [ ] Rules preview shows before applying
- [ ] Project-specific isolation maintained
- [ ] Cursor AI follows uploaded team standards

---

## 🔄 Development Flow

1. **Read IMPLEMENTATION_GUIDE_v2.md section for current step**
2. **Implement using exact patterns from Phase 1**
3. **Test immediately with various file types**
4. **Check off the item in CURSOR_AI_CHECKLIST.md**
5. **Move to next step**

**Remember:** Phase 1 proved the architecture works perfectly. Phase 2 builds on that foundation using identical patterns for file operations, error handling, and UI integration.

---

**BEGIN WITH:** Step 2.1 - Style Guide Upload Handler (shown above)

**SUCCESS FOUNDATION:** You have a working, tested system. Extend it using the exact same patterns that made Phase 1 successful. The architecture is proven - now add the style guide features following the established blueprints.

**FILE REFERENCES:**
- Implementation details: `IMPLEMENTATION_GUIDE_v2.md`
- Code patterns: `CURSOR_IMPLEMENTATION_GUIDE.md`  
- Feature specs: `FEATURE_ROADMAP_v2.md`
- Step-by-step: `CURSOR_AI_CHECKLIST.md`

You have everything needed. Build with confidence! 🚀 