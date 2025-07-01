#!/bin/bash

# Auto-Brainlift Demo Preparation Script
# This script prepares the app for a quick demo deployment

echo "🚀 Preparing Auto-Brainlift for Demo Deployment..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the auto-brainlift directory"
    exit 1
fi

# Step 1: Install electron-builder
echo "📦 Installing electron-builder..."
npm install --save-dev electron-builder

# Step 2: Update package.json with build configuration
echo "📝 Updating package.json with build configuration..."
cat > package.json.tmp << 'EOF'
{
  "name": "auto-brainlift",
  "private": true,
  "version": "1.0.0",
  "description": "Automatically generate development summaries after Git commits",
  "main": "electron/main.js",
  "scripts": {
    "start": "electron .",
    "dev": "electron .",
    "test": "echo \"Tests will be added\" && exit 0",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux"
  },
  "keywords": [
    "electron",
    "git",
    "ai",
    "summarization"
  ],
  "author": "Auto-Brainlift Team",
  "license": "MIT",
  "devDependencies": {
    "electron": "^30.0.1",
    "electron-builder": "^24.13.3"
  },
  "dependencies": {
    "electron-settings": "^4.0.4",
    "uuid": "^11.1.0"
  },
  "build": {
    "appId": "com.autobrainlift.app",
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
      "!*.pyc",
      "!.git",
      "!.gitignore",
      "!node_modules/.cache"
    ],
    "mac": {
      "category": "public.app-category.developer-tools",
      "icon": "build/icon.png"
    },
    "win": {
      "target": "nsis",
      "icon": "build/icon.png"
    },
    "linux": {
      "target": ["AppImage"],
      "icon": "build/icon.png"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  }
}
EOF

mv package.json.tmp package.json

# Step 3: Create build directory and placeholder icon
echo "🎨 Creating build assets..."
mkdir -p build
if [ ! -f "build/icon.png" ]; then
    # Create a simple placeholder icon using ImageMagick if available
    if command -v convert &> /dev/null; then
        convert -size 512x512 xc:lightblue -fill black -gravity center -pointsize 72 -annotate +0+0 'AB' build/icon.png
        echo "✅ Created placeholder icon"
    else
        echo "⚠️  Please add a 512x512 PNG icon at build/icon.png"
    fi
fi

# Step 4: Clean up Python cache
echo "🧹 Cleaning up Python cache..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Step 5: Create .env.example file
echo "📄 Creating .env.example..."
cat > .env.example << 'EOF'
# Copy this file to .env and add your API key
OPENAI_API_KEY=your_openai_api_key_here
EOF

# Step 6: Create quick demo instructions
echo "📋 Creating demo instructions..."
cat > DEMO_INSTRUCTIONS.md << 'EOF'
# Auto-Brainlift Demo Instructions

## Quick Setup for Demo

1. **Set up API Key**:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key

2. **Build the App**:
   ```bash
   npm run build
   ```

3. **Find the Installer**:
   - Look in the `dist/` folder
   - macOS: `Auto-Brainlift-1.0.0.dmg`
   - Windows: `Auto-Brainlift Setup 1.0.0.exe`
   - Linux: `Auto-Brainlift-1.0.0.AppImage`

4. **Install and Run**:
   - Install the app like any other desktop application
   - On first run, enter your OpenAI API key when prompted

## Demo Talking Points

- **Automatic Git Integration**: Watches for commits and generates summaries
- **AI-Powered Analysis**: Uses GPT-4 to understand code changes
- **Multi-Agent System**: Security, quality, and documentation agents
- **Smart Caching**: Reduces API costs with intelligent caching
- **Project Management**: Handle multiple projects from one interface

## Known Limitations (Demo Version)

- No code signing (users will see security warnings)
- Python must be installed on the system
- Manual API key entry required
- No auto-update functionality yet

## Troubleshooting

If the app doesn't start:
1. Check that Python 3.8+ is installed
2. Verify the API key is correct
3. Check logs in: `~/Library/Application Support/auto-brainlift/logs/`
EOF

echo "✅ Demo preparation complete!"
echo ""
echo "Next steps:"
echo "1. Add your icon to build/icon.png (512x512 PNG)"
echo "2. Run: npm run build"
echo "3. Find installer in dist/ folder"
echo "4. Share with your boss!"
echo ""
echo "For more details, see DEMO_INSTRUCTIONS.md" 