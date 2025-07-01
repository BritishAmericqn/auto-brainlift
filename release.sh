#!/bin/bash

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.1"
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
rm -rf dist/ build/
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Run tests if they exist
if [ -f "test_agent.py" ]; then
    echo "🧪 Running tests..."
    python3 test_agent.py
fi

# Commit version bump
echo "💾 Committing version bump..."
git add package.json
git commit -m "chore: Bump version to $VERSION"

# Create tag
echo "🏷️  Creating git tag v$VERSION..."
git tag "v$VERSION"

# Build
echo "🔨 Building application..."
npm run build

echo ""
echo "✅ Release $VERSION prepared successfully!"
echo ""
echo "📦 Build artifacts:"
ls -lh dist/*.dmg 2>/dev/null || echo "No DMG found"
ls -lh dist/*.exe 2>/dev/null || echo "No EXE found"
ls -lh dist/*.AppImage 2>/dev/null || echo "No AppImage found"
echo ""
echo "📋 Next steps:"
echo "1. Test the build: open dist/*.dmg"
echo "2. Push to git: git push && git push origin v$VERSION"
echo "3. Create GitHub release and upload installers"
echo "4. Notify users about the update"
echo ""
echo "💡 Tip: Set up GitHub Actions for automated releases!" 