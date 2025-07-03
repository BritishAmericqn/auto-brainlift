#!/bin/bash

echo "🧪 Testing Auto-Brainlift build configuration..."
echo "============================================"

# Check Node.js version
echo "📦 Node.js version:"
node --version
if [ $? -ne 0 ]; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
echo ""
echo "📦 npm version:"
npm --version

# Check Python
echo ""
echo "🐍 Python version:"
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check ImageMagick
echo ""
echo "🎨 ImageMagick:"
if command -v convert &> /dev/null; then
    convert --version | head -n1
else
    echo "⚠️  Not installed (optional, needed for icon generation)"
    echo "   Install with: brew install imagemagick"
fi

# Check GitHub CLI
echo ""
echo "🚀 GitHub CLI:"
if command -v gh &> /dev/null; then
    gh --version | head -n1
else
    echo "⚠️  Not installed (optional, helps with releases)"
    echo "   Install with: brew install gh"
fi

# Check electron-builder
echo ""
echo "🔨 Electron Builder:"
if [ -f "node_modules/.bin/electron-builder" ]; then
    echo "✅ Installed"
else
    echo "❌ Not installed. Run: npm install"
fi

# Check build directory
echo ""
echo "📁 Build directory:"
if [ -d "build" ]; then
    echo "✅ Exists"
    if [ -f "build/icon.png" ]; then
        echo "   ✅ icon.png found"
    else
        echo "   ⚠️  icon.png missing - run: cd build && ./generate-icons.sh"
    fi
else
    echo "❌ Missing build directory"
fi

# Check package.json
echo ""
echo "📋 Package configuration:"
if [ -f "package.json" ]; then
    VERSION=$(node -p "require('./package.json').version")
    echo "   Version: $VERSION"
    echo "   App ID: com.autobrainlift.app"
    echo "   Product Name: Auto-Brainlift"
else
    echo "❌ package.json not found"
fi

echo ""
echo "============================================"
echo "✅ Build configuration check complete!"
echo ""
echo "📝 Next steps:"
echo "1. Run 'npm install' if needed"
echo "2. Generate icons: cd build && ./generate-icons.sh"
echo "3. Build: npm run build:mac (or build:win/build:linux)"
echo "4. Or use release script: ./release.sh <version>" 