# GitHub Releases Guide for Auto-Brainlift

## 🚀 Why GitHub Releases?

- **Free hosting** for your installers (up to 2GB per file)
- **Direct download links** that never expire
- **Version management** with release notes
- **Download statistics** to track adoption
- **Professional appearance** for your project
- **Auto-updater compatible** (for future implementation)

## 📋 Prerequisites

1. GitHub repository for your project
2. Built installers (DMG, EXE, etc.)
3. Git tags for version tracking

## 🔧 Initial Setup

### 1. Create GitHub Repository (if not done)

```bash
# Initialize git in your project
cd auto-brainlift
git init

# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/auto-brainlift.git

# First commit
git add .
git commit -m "Initial commit: Auto-Brainlift v1.0.0"
git push -u origin main
```

### 2. Create Your First Release

#### Option A: Via GitHub Web Interface (Easiest)

1. Go to your repo: `https://github.com/YOUR_USERNAME/auto-brainlift`
2. Click **"Releases"** (right side of page)
3. Click **"Create a new release"**
4. Fill in:
   - **Tag**: `v1.0.0` (create new tag)
   - **Release title**: `Auto-Brainlift v1.0.0`
   - **Description**: See template below
5. **Attach binaries**: Drag and drop your DMG/EXE files
6. Click **"Publish release"**

#### Option B: Via GitHub CLI (Automated)

```bash
# Install GitHub CLI (one time)
brew install gh

# Authenticate (one time)
gh auth login

# Create release with files
gh release create v1.0.0 \
  --title "Auto-Brainlift v1.0.0" \
  --notes-file RELEASE_NOTES.md \
  dist/Auto-Brainlift-*.dmg \
  dist/Auto-Brainlift-*.exe
```

## 📝 Release Description Template

Create `RELEASE_TEMPLATE.md`:

```markdown
# Auto-Brainlift v1.0.0

AI-powered Git commit summaries for better development documentation.

## 🎯 Features
- Automatic summary generation after Git commits
- Multi-agent analysis (Security, Quality, Documentation)
- Smart caching to reduce API costs
- Cursor chat integration
- Project management support

## 📦 Downloads

| Platform | File | Requirements |
|----------|------|--------------|
| macOS | `Auto-Brainlift-1.0.0-arm64.dmg` | macOS 10.13+, Python 3.8+ |
| Windows | `Auto-Brainlift-Setup-1.0.0.exe` | Windows 10+, Python 3.8+ |
| Linux | `Auto-Brainlift-1.0.0.AppImage` | Python 3.8+ |

## 🚀 Installation

### macOS
1. Download the DMG file
2. Double-click to mount
3. Drag Auto-Brainlift to Applications
4. First run: Right-click → Open (to bypass Gatekeeper)

### Windows
1. Download the EXE installer
2. Run the installer
3. Follow installation wizard

### All Platforms
- **Requires**: Python 3.8+ installed
- **First run**: Enter your OpenAI API key when prompted
- **Note**: Python dependencies will auto-install on first run

## 🐛 Known Issues
- macOS users will see "unidentified developer" warning (right-click → Open)
- First run may take 1-2 minutes to install Python dependencies

## 📝 Changelog
- Initial release
- Multi-agent system (Security, Quality, Documentation)
- Smart caching system
- Cursor chat integration
- Multi-project support

## 🤝 Getting Started
1. Install the app
2. Enter your OpenAI API key
3. Open a Git repository
4. Make commits and watch the magic happen!

---
**Need help?** Open an issue on GitHub
```

## 🎯 Quick Release Workflow

### 1. Build Your App
```bash
npm run build
```

### 2. Create Release
```bash
# Using the release script
./release.sh 1.0.0

# Push tags
git push && git push origin v1.0.0

# Create GitHub release
gh release create v1.0.0 \
  --title "Auto-Brainlift v1.0.0" \
  --notes "See RELEASE_NOTES.md for details" \
  dist/*.dmg dist/*.exe dist/*.AppImage
```

### 3. Share Download Link
Your releases will be at:
```
https://github.com/YOUR_USERNAME/auto-brainlift/releases
```

Direct download links:
```
https://github.com/YOUR_USERNAME/auto-brainlift/releases/download/v1.0.0/Auto-Brainlift-1.0.0-arm64.dmg
```

## 🔄 Automated Releases with GitHub Actions

Create `.github/workflows/release.yml`:

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        os: [macos-latest, windows-latest, ubuntu-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Upload to Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/*.dmg
            dist/*.exe
            dist/*.AppImage
            dist/*.zip
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 💡 Pro Tips

### 1. Semantic Versioning
- `1.0.0` → `1.0.1`: Bug fixes
- `1.0.0` → `1.1.0`: New features
- `1.0.0` → `2.0.0`: Breaking changes

### 2. Pre-releases
For beta testing:
```bash
gh release create v1.0.0-beta.1 --prerelease
```

### 3. Release Assets Naming
Keep consistent naming:
- `Auto-Brainlift-{version}-{arch}.dmg`
- `Auto-Brainlift-Setup-{version}.exe`
- `Auto-Brainlift-{version}.AppImage`

### 4. Update README
Add download badges to your README.md:
```markdown
[![Download](https://img.shields.io/github/v/release/YOUR_USERNAME/auto-brainlift)](https://github.com/YOUR_USERNAME/auto-brainlift/releases)
[![Downloads](https://img.shields.io/github/downloads/YOUR_USERNAME/auto-brainlift/total)](https://github.com/YOUR_USERNAME/auto-brainlift/releases)
```

## 🚀 Future: Auto-Updates

GitHub Releases works perfectly with electron-updater:

1. Install: `npm install electron-updater`
2. Configure in package.json:
```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "YOUR_USERNAME",
      "repo": "auto-brainlift"
    }
  }
}
```
3. Users will auto-update from GitHub Releases! 