# Auto-Brainlift Update Workflow

## 📝 What to Include in Git

### ✅ **DO Commit**:
- All source code (`agents/`, `electron/`, etc.)
- Configuration files (`package.json`, `requirements.txt`)
- Documentation (`*.md` files)
- Scripts (`prepare-for-demo.sh`, `build-python.js`)
- HTML/CSS/JS files
- Prompts and templates

### ❌ **DON'T Commit** (already in .gitignore):
- `dist/` folder (build outputs)
- `build/` folder (build assets)
- `node_modules/`
- `venv/` (Python virtual environment)
- `__pycache__/`
- `.env` (API keys)
- `*.dmg`, `*.exe`, `*.zip` (installers)
- Generated logs and outputs

## 🔄 Update Process

### 1. **Make Your Changes**
```bash
# Make code changes
# Test locally with:
npm start
```

### 2. **Update Version Number**
Edit `package.json`:
```json
{
  "version": "1.0.1",  // Increment this
  ...
}
```

Version numbering guide:
- `1.0.x` - Bug fixes only
- `1.x.0` - New features (backwards compatible)
- `x.0.0` - Major changes (breaking changes)

### 3. **Commit Your Changes**
```bash
git add .
git commit -m "feat: Add new feature X"
git push
```

### 4. **Tag the Release** (Optional but recommended)
```bash
git tag v1.0.1
git push origin v1.0.1
```

### 5. **Build New Release**
```bash
# Clean old builds
rm -rf dist/

# Build for current platform
npm run build

# Or build for all platforms
npm run build:mac
npm run build:win
npm run build:linux
```

### 6. **Distribute Update**

#### Option A: Manual Distribution
1. Upload new DMG/installer to same location
2. Notify users to download new version
3. Users manually replace old version

#### Option B: GitHub Releases (Recommended)
1. Go to GitHub repo → Releases → Create new release
2. Use the git tag (e.g., v1.0.1)
3. Upload the installers from `dist/`
4. Write release notes
5. Publish release

## 📋 Release Checklist

Before each release:
- [ ] Test on clean machine
- [ ] Update version in `package.json`
- [ ] Update any documentation
- [ ] Clear Python cache: `find . -name "__pycache__" -type d -exec rm -rf {} +`
- [ ] Test build locally
- [ ] Create git tag
- [ ] Build final release
- [ ] Upload to distribution channel
- [ ] Update download links/documentation

## 🚀 Quick Release Script

Create `release.sh`:
```bash
#!/bin/bash
VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.1"
    exit 1
fi

echo "🚀 Releasing version $VERSION"

# Update package.json version
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json

# Clean
rm -rf dist/ build/
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Commit version bump
git add package.json
git commit -m "chore: Bump version to $VERSION"

# Tag
git tag "v$VERSION"

# Build
npm run build

echo "✅ Build complete!"
echo "📦 Installers in dist/"
echo "🏷️  Tagged as v$VERSION"
echo ""
echo "Next steps:"
echo "1. git push && git push origin v$VERSION"
echo "2. Upload dist/*.dmg to distribution"
echo "3. Create GitHub release (if using GitHub)"
```

## 🔮 Future: Auto-Updates

When ready for production, implement auto-updates:

1. Install electron-updater:
```bash
npm install electron-updater
```

2. Set up update server (GitHub Releases works great)

3. Add to main.js:
```javascript
const { autoUpdater } = require('electron-updater');

app.on('ready', () => {
  autoUpdater.checkForUpdatesAndNotify();
});
```

4. Users will automatically get updates!

## 📊 Semantic Commit Messages

Use conventional commits for clear history:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/tooling changes

Example:
```bash
git commit -m "feat: Add real-time cache statistics display"
git commit -m "fix: Resolve Python path issue on Windows"
git commit -m "docs: Update installation instructions"
``` 