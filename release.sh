#!/bin/bash

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.3"
    exit 1
fi

echo "🚀 Releasing Auto-Brainlift version $VERSION"
echo "========================================="

# Update package.json version
echo "📝 Updating version in package.json..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json
else
    # Linux
    sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json
fi

# Clean old builds
echo "🧹 Cleaning old builds..."
rm -rf dist/ 
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Generate icons if ImageMagick is available
if command -v convert &> /dev/null && command -v iconutil &> /dev/null; then
    echo "🎨 Generating icons..."
    cd build
    ./generate-icons.sh
    cd ..
else
    echo "⚠️  Skipping icon generation (ImageMagick not installed)"
    echo "   Install with: brew install imagemagick"
fi

# Run tests if they exist
if [ -f "test_agent.py" ]; then
    echo "🧪 Running tests..."
    python3 test_agent.py || { echo "❌ Tests failed!"; exit 1; }
fi

# Install npm dependencies
echo "📦 Installing dependencies..."
npm install

# Commit version bump
echo "💾 Committing version bump..."
git add package.json package-lock.json
git commit -m "chore: Bump version to $VERSION" || true

# Create tag
echo "🏷️  Creating git tag v$VERSION..."
git tag -f "v$VERSION"

# Build for current platform
echo "🔨 Building application..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - build universal binary
    npm run build:mac
    
    # Check if code signing is available
    if security find-identity -v -p codesigning | grep -q "Developer ID"; then
        echo "✍️  Code signing is available"
    else
        echo "⚠️  No code signing certificate found"
        echo "   The app will require Gatekeeper approval on first run"
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    npm run build:linux
else
    # Windows (via Git Bash or WSL)
    npm run build:win
fi

echo ""
echo "✅ Release $VERSION prepared successfully!"
echo ""
echo "📦 Build artifacts:"
ls -lh dist/*.dmg 2>/dev/null && echo "  ✓ macOS DMG ready"
ls -lh dist/*.zip 2>/dev/null && echo "  ✓ macOS ZIP ready"
ls -lh dist/*.exe 2>/dev/null && echo "  ✓ Windows installer ready"
ls -lh dist/*.AppImage 2>/dev/null && echo "  ✓ Linux AppImage ready"
ls -lh dist/*.deb 2>/dev/null && echo "  ✓ Linux DEB ready"
echo ""

# Create release notes
echo "📝 Creating release notes..."
cat > RELEASE_NOTES_v${VERSION}.md << EOF
# Auto-Brainlift v${VERSION}

## 🎯 What's New
- [Add your changes here]

## 📦 Downloads

| Platform | File | SHA256 |
|----------|------|--------|
EOF

# Add checksums for each artifact
if ls dist/*.dmg 1> /dev/null 2>&1; then
    for file in dist/*.dmg; do
        filename=$(basename "$file")
        checksum=$(shasum -a 256 "$file" | cut -d' ' -f1)
        echo "| macOS | \`$filename\` | \`$checksum\` |" >> RELEASE_NOTES_v${VERSION}.md
    done
fi

if ls dist/*.exe 1> /dev/null 2>&1; then
    for file in dist/*.exe; do
        filename=$(basename "$file")
        checksum=$(shasum -a 256 "$file" | cut -d' ' -f1)
        echo "| Windows | \`$filename\` | \`$checksum\` |" >> RELEASE_NOTES_v${VERSION}.md
    done
fi

if ls dist/*.AppImage 1> /dev/null 2>&1; then
    for file in dist/*.AppImage; do
        filename=$(basename "$file")
        checksum=$(shasum -a 256 "$file" | cut -d' ' -f1)
        echo "| Linux | \`$filename\` | \`$checksum\` |" >> RELEASE_NOTES_v${VERSION}.md
    done
fi

echo "" >> RELEASE_NOTES_v${VERSION}.md
echo "## 🚀 Installation" >> RELEASE_NOTES_v${VERSION}.md
echo "See [README](README.md) for installation instructions." >> RELEASE_NOTES_v${VERSION}.md

echo ""
echo "📋 Next steps:"
echo "1. Edit release notes: RELEASE_NOTES_v${VERSION}.md"
echo "2. Test the build locally"
echo "3. Push to GitHub: git push && git push origin v$VERSION"
echo ""

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo "🚀 GitHub CLI detected! To create a release:"
    echo ""
    echo "gh release create v$VERSION \\"
    echo "  --title \"Auto-Brainlift v$VERSION\" \\"
    echo "  --notes-file RELEASE_NOTES_v${VERSION}.md \\"
    echo "  dist/*.dmg dist/*.exe dist/*.AppImage dist/*.deb dist/*.zip"
else
    echo "💡 Install GitHub CLI for easier releases:"
    echo "   brew install gh"
    echo ""
    echo "Or manually create release at:"
    echo "   https://github.com/YOUR_USERNAME/auto-brainlift/releases/new"
fi 