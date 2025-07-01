# Auto-Brainlift v1.0.2

🚀 **Cursor Rules Integration Release**

New feature that enhances AI assistant capabilities in Cursor IDE!

## ✨ New Features

- **Cursor Rules Integration**: Auto-Brainlift now creates project-specific rules for Cursor IDE
  - AI assistants automatically understand your project context
  - Reads your brainlifts, context logs, and error logs
  - Enable/disable from Settings → Cursor Rules Integration
  - Choose between Always, Auto Attached, or Manual rule types
- **Git Integration Improvements**: Better handling of git hooks and automation
- **UI Enhancements**: Improved settings panel with new Cursor Rules section

## 🔄 Changes

- Added `.cursor/` to .gitignore - cursor rules are now user-specific
- Improved project management and switching
- Enhanced documentation with CURSOR_RULES_INTEGRATION.md guide
- Better error handling for multi-agent analysis

## 📦 Installation

### macOS
1. Download `Auto-Brainlift-1.0.2-arm64.dmg`
2. Double-click to mount
3. Drag Auto-Brainlift to Applications
4. First run: Right-click → Open (bypasses security warning)

### Updating from Previous Versions
Simply download and install the new version - it will replace the old one. Your settings and projects will be preserved.

### New Cursor Rules Feature
After updating:
1. Open Settings (gear icon)
2. Scroll to "Cursor Rules Integration"
3. Enable and select your preferred rule type
4. Restart Cursor IDE to activate

---

# Auto-Brainlift v1.0.1

🎨 **UI Updates Release**

Minor improvements and bug fixes to the user interface.

## 🔄 Changes

- **UI Improvements**: Updated user interface for better user experience
- **Bug Fixes**: Various minor fixes and improvements

## 📦 Installation

### macOS
1. Download `Auto-Brainlift-1.0.1-arm64.dmg`
2. Double-click to mount
3. Drag Auto-Brainlift to Applications
4. First run: Right-click → Open (bypasses security warning)

### Updating from v1.0.0
Simply download and install the new version - it will replace the old one.

---

# Auto-Brainlift v1.0.0

🎉 **First Release!**

AI-powered Git commit summaries for better development documentation.

## ✨ Features

- **Automatic Summary Generation**: Creates comprehensive summaries after each Git commit
- **Multi-Agent Analysis**: 
  - 🔒 Security Agent: Identifies potential security issues
  - ✅ Quality Agent: Analyzes code quality and best practices
  - 📚 Documentation Agent: Checks documentation completeness
- **Smart Caching**: Reduces API costs by up to 70% with intelligent caching
- **Cursor Chat Integration**: Incorporates your Cursor editor conversations into summaries
- **Multi-Project Support**: Manage multiple projects from one interface
- **Budget Management**: Set token limits per commit to control costs

## 📦 Installation

### macOS
1. Download `Auto-Brainlift-1.0.0-arm64.dmg`
2. Double-click to mount
3. Drag Auto-Brainlift to Applications
4. First run: Right-click → Open (bypasses security warning)

### Requirements
- Python 3.8 or later
- OpenAI API key
- Git installed

## 🚀 Getting Started

1. Launch Auto-Brainlift
2. Enter your OpenAI API key when prompted
3. Add your Git project
4. Make commits and watch the AI generate summaries!

## ⚠️ Known Limitations

- Requires Python to be installed separately
- First run will install Python dependencies (1-2 minutes)
- macOS users will see "unidentified developer" warning (normal for unsigned apps)

## 🔮 Coming Soon

- Bundled Python runtime (no separate installation needed)
- Auto-update functionality
- Code signing for smoother installation
- Windows and Linux builds

---

**Questions?** Open an issue on GitHub
**Found a bug?** Please report it!

Thank you for trying Auto-Brainlift! 🚀 