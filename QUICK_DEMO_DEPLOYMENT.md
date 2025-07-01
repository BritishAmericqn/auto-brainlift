# Quick Demo Deployment Guide for Auto-Brainlift

## 🚀 Fastest Path to Demo (5 minutes)

### 1. Prepare for Build
```bash
cd auto-brainlift
chmod +x prepare-for-demo.sh
./prepare-for-demo.sh
```

### 2. Add an Icon (Optional but Recommended)
Create a 512x512 PNG icon and save it as `build/icon.png`

### 3. Build the App
```bash
npm run build
```

### 4. Find Your Installer
Look in the `dist/` folder:
- **macOS**: `Auto-Brainlift-1.0.0.dmg`
- **Windows**: `Auto-Brainlift Setup 1.0.0.exe`  
- **Linux**: `Auto-Brainlift-1.0.0.AppImage`

### 5. Share with Your Boss
Upload to:
- Google Drive / Dropbox (easiest)
- Company file server
- GitHub Releases (if you have a repo)

## ⚠️ Important Notes for Demo

### What Users Need:
1. **Python 3.8+** must be installed on their system
2. **OpenAI API Key** (they'll be prompted on first run)
3. **Git** installed for the app to work with repositories

### Known Demo Limitations:
- Users will see security warnings (app isn't code-signed)
- Python dependencies will auto-install on first run (may take a minute)
- No auto-update functionality yet

### Demo Talking Points:
✅ **AI-Powered**: Uses GPT-4 to understand code changes  
✅ **Multi-Agent System**: Security, quality, and documentation analysis  
✅ **Smart Caching**: Reduces API costs by ~70%  
✅ **Project Management**: Handle multiple projects easily  
✅ **Cursor Integration**: Incorporates chat context into summaries  

## 🔧 Troubleshooting

If the app doesn't work on demo:

1. **"Python not found" error**
   - Ensure Python 3.8+ is installed
   - Windows: Check Python is in PATH

2. **"Cannot find module" errors**
   - Dependencies are auto-installing, wait a moment
   - Check internet connection

3. **App won't open (macOS)**
   - Right-click → Open (bypasses Gatekeeper)
   - System Preferences → Security → Allow

4. **Check logs**:
   - macOS: `~/Library/Application Support/auto-brainlift/logs/`
   - Windows: `%APPDATA%/auto-brainlift/logs/`

## 📊 For Production Release

When ready for full deployment:
1. Code sign the application ($99/year for Apple, ~$200/year for Windows)
2. Implement auto-updater
3. Bundle Python runtime (using PyInstaller)
4. Add telemetry and crash reporting
5. Create proper installer with custom UI

See `PRODUCTION_DEPLOYMENT_GUIDE.md` for detailed instructions. 