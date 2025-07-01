# Auto-Brainlift Production Deployment Guide

## Overview
Auto-Brainlift is an Electron desktop application with a Python backend that needs special considerations for production deployment due to its hybrid architecture.

## 1. Pre-Deployment Checklist

### Security & API Keys
- [ ] Remove all hardcoded API keys from source code
- [ ] Implement secure credential storage using electron-store
- [ ] Add API key validation on app startup
- [ ] Implement rate limiting for OpenAI API calls
- [ ] Add error handling for expired/invalid API keys

### Code Quality
- [ ] Run security audit: `npm audit`
- [ ] Fix all critical vulnerabilities
- [ ] Test on all target platforms (Windows, macOS, Linux)
- [ ] Add comprehensive error logging
- [ ] Implement crash reporting (e.g., Sentry)
- [ ] Add telemetry for usage analytics (with user consent)

### Python Integration
- [ ] Bundle Python runtime with the app
- [ ] Ensure all Python dependencies are included
- [ ] Test Python script execution on clean systems
- [ ] Handle Python environment setup errors gracefully

## 2. Building for Production

### Update package.json with Build Scripts
```json
{
  "scripts": {
    "start": "electron .",
    "dev": "electron .",
    "test": "echo \"Tests will be added\" && exit 0",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac", 
    "build:linux": "electron-builder --linux",
    "dist": "electron-builder -mwl"
  },
  "build": {
    "appId": "com.yourcompany.autobrainlift",
    "productName": "Auto-Brainlift",
    "directories": {
      "output": "dist"
    },
    "files": [
      "electron/**/*",
      "index.html",
      "public/**/*",
      "agents/**/*",
      "prompts/**/*",
      "package.json",
      "!**/__pycache__",
      "!venv",
      "!*.pyc"
    ],
    "extraResources": [
      {
        "from": "python-dist",
        "to": "python-dist",
        "filter": ["**/*"]
      }
    ],
    "mac": {
      "category": "public.app-category.developer-tools",
      "icon": "build/icon.icns",
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "build/entitlements.mac.plist",
      "entitlementsInherit": "build/entitlements.mac.plist",
      "notarize": {
        "teamId": "YOUR_TEAM_ID"
      }
    },
    "win": {
      "target": "nsis",
      "icon": "build/icon.ico"
    },
    "linux": {
      "target": ["AppImage", "deb"],
      "icon": "build/icon.png"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  }
}
```

### Install Build Dependencies
```bash
npm install --save-dev electron-builder
npm install --save-dev @electron/notarize  # For macOS notarization
```

## 3. Python Bundling Strategy

### Option A: Bundle Python Runtime (Recommended)
1. Use PyInstaller to create standalone Python executables:
```bash
pip install pyinstaller
pyinstaller --onefile --distpath python-dist agents/langgraph_agent.py
```

2. Create a build script to automate Python bundling:
```javascript
// build-python.js
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function buildPython() {
  console.log('Building Python executables...');
  
  // Create python-dist directory
  if (!fs.existsSync('python-dist')) {
    fs.mkdirSync('python-dist');
  }
  
  // Build main agent
  execSync('pyinstaller --onefile --distpath python-dist agents/langgraph_agent.py');
  
  // Copy other necessary Python files
  // ...
}

buildPython();
```

### Option B: Require Python Installation
- Check for Python on startup
- Provide installation instructions
- Auto-install dependencies on first run

## 4. App Configuration

### Create Production Config
```javascript
// config/production.js
module.exports = {
  api: {
    openai: {
      endpoint: process.env.OPENAI_API_ENDPOINT || 'https://api.openai.com/v1',
      timeout: 30000,
      maxRetries: 3
    }
  },
  cache: {
    maxSize: 100 * 1024 * 1024, // 100MB
    ttl: 30 * 24 * 60 * 60 * 1000 // 30 days
  },
  logging: {
    level: 'error',
    maxFiles: 5,
    maxSize: '10m'
  }
};
```

## 5. Code Signing & Notarization

### macOS
1. Get Apple Developer Certificate
2. Configure electron-builder for code signing
3. Set up notarization credentials:
```bash
export APPLE_ID="your-apple-id@example.com"
export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="YOUR_TEAM_ID"
```

### Windows
1. Get Code Signing Certificate
2. Configure electron-builder:
```json
{
  "win": {
    "certificateFile": "path/to/certificate.pfx",
    "certificatePassword": "YOUR_CERT_PASSWORD"
  }
}
```

## 6. Auto-Update Implementation

### Add Auto-Updater
```javascript
// electron/updater.js
const { autoUpdater } = require('electron-updater');
const { dialog } = require('electron');

function setupAutoUpdater() {
  autoUpdater.checkForUpdatesAndNotify();
  
  autoUpdater.on('update-available', () => {
    dialog.showMessageBox({
      type: 'info',
      title: 'Update available',
      message: 'A new version of Auto-Brainlift is available. It will be downloaded in the background.',
      buttons: ['OK']
    });
  });
  
  autoUpdater.on('update-downloaded', () => {
    dialog.showMessageBox({
      type: 'info',
      title: 'Update ready',
      message: 'Update downloaded. The application will restart to apply the update.',
      buttons: ['Restart Now', 'Later']
    }).then((result) => {
      if (result.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
  });
}

module.exports = { setupAutoUpdater };
```

## 7. Distribution

### GitHub Releases (Recommended for Demo)
1. Create GitHub repository (if not already)
2. Set up GitHub Actions for automated builds:
```yaml
# .github/workflows/build.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          npm ci
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build Python
        run: node build-python.js
      
      - name: Build Electron App
        run: npm run build
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.os }}-build
          path: dist/*
```

### Other Distribution Options
- **Mac App Store**: Requires additional sandboxing
- **Microsoft Store**: Use electron-builder's appx target
- **Linux**: Snap Store, Flatpak
- **Direct Download**: Host installers on your website

## 8. First-Run Experience

### Create Onboarding Flow
```javascript
// electron/onboarding.js
const { dialog } = require('electron');
const settings = require('electron-settings');

async function checkFirstRun() {
  const hasRunBefore = await settings.has('hasRunBefore');
  
  if (!hasRunBefore) {
    // Show welcome dialog
    dialog.showMessageBox({
      type: 'info',
      title: 'Welcome to Auto-Brainlift!',
      message: 'Let\'s set up your development environment.',
      buttons: ['Get Started']
    });
    
    // Guide through API key setup
    const apiKey = await promptForAPIKey();
    await settings.set('openaiApiKey', apiKey);
    
    // Set up Git hooks
    await setupGitHooks();
    
    await settings.set('hasRunBefore', true);
  }
}
```

## 9. Error Handling & Crash Reporting

### Implement Global Error Handler
```javascript
// electron/errorHandler.js
const { app, dialog } = require('electron');
const fs = require('fs');
const path = require('path');

function setupErrorHandling() {
  process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    logError(error);
    
    dialog.showErrorBox(
      'Unexpected Error',
      'Auto-Brainlift encountered an error. Please restart the application.'
    );
    
    app.quit();
  });
  
  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    logError(new Error(`Unhandled Rejection: ${reason}`));
  });
}

function logError(error) {
  const logPath = path.join(app.getPath('userData'), 'crash-logs');
  fs.mkdirSync(logPath, { recursive: true });
  
  const timestamp = new Date().toISOString();
  const logFile = path.join(logPath, `crash-${timestamp}.log`);
  
  fs.writeFileSync(logFile, `
    Time: ${timestamp}
    Error: ${error.message}
    Stack: ${error.stack}
    Platform: ${process.platform}
    Version: ${app.getVersion()}
  `);
}
```

## 10. Testing Checklist

### Pre-Release Testing
- [ ] Fresh install on clean VMs for each platform
- [ ] Test without Python pre-installed
- [ ] Test with various Git configurations
- [ ] Test API key input and validation
- [ ] Test cache functionality
- [ ] Test auto-update mechanism
- [ ] Verify all file paths work correctly
- [ ] Test with different screen resolutions
- [ ] Verify memory usage is reasonable
- [ ] Test offline functionality

## 11. Quick Start for Demo

For a quick demo deployment:

1. **Install electron-builder**:
   ```bash
   npm install --save-dev electron-builder
   ```

2. **Create basic icons** (required for building):
   - macOS: 512x512 PNG → convert to .icns
   - Windows: 256x256 PNG → convert to .ico
   - Linux: 512x512 PNG

3. **Build for current platform**:
   ```bash
   npm run build
   ```

4. **Find installer** in `dist/` folder

5. **Share via**:
   - GitHub Releases (easiest)
   - Google Drive/Dropbox
   - Company file server

## Next Steps

1. Start with basic build configuration
2. Test on target platforms
3. Implement auto-updater for easy updates
4. Add crash reporting for production monitoring
5. Set up CI/CD for automated builds

Remember: For initial demos, you can skip code signing (users will see security warnings but can still install). 