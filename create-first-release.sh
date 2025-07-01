#!/bin/bash

echo "🚀 Auto-Brainlift First Release Helper"
echo "======================================"
echo ""

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository!"
    echo "Please run: git init"
    exit 1
fi

# Check if DMG exists
if ! ls dist/*.dmg >/dev/null 2>&1; then
    echo "❌ No DMG file found in dist/"
    echo "Please run: npm run build"
    exit 1
fi

# Get the DMG filename
DMG_FILE=$(ls dist/*.dmg | head -1)
echo "✅ Found installer: $DMG_FILE"

# Check GitHub CLI auth
if ! gh auth status >/dev/null 2>&1; then
    echo ""
    echo "📋 GitHub CLI not authenticated. Let's fix that:"
    echo "Running: gh auth login"
    gh auth login
fi

echo ""
echo "📝 Step-by-step GitHub Release Creation"
echo "--------------------------------------"
echo ""

# Step 1: Ensure remote is set
echo "1️⃣ Checking GitHub remote..."
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "❌ No GitHub remote found!"
    echo ""
    echo "Please:"
    echo "1. Create a new repository on GitHub.com"
    echo "2. Run: git remote add origin https://github.com/YOUR_USERNAME/auto-brainlift.git"
    echo "3. Run this script again"
    exit 1
fi

REMOTE_URL=$(git remote get-url origin)
echo "✅ Remote: $REMOTE_URL"

# Step 2: Commit all changes
echo ""
echo "2️⃣ Checking for uncommitted changes..."
if [[ -n $(git status -s) ]]; then
    echo "📦 You have uncommitted changes. Let's commit them:"
    git add .
    git commit -m "feat: Add production build configuration and deployment"
    echo "✅ Changes committed!"
else
    echo "✅ No uncommitted changes"
fi

# Step 3: Push to GitHub
echo ""
echo "3️⃣ Pushing to GitHub..."
git push -u origin main || git push -u origin master

# Step 4: Create tag
echo ""
echo "4️⃣ Creating version tag..."
if git rev-parse v1.0.0 >/dev/null 2>&1; then
    echo "⚠️  Tag v1.0.0 already exists"
else
    git tag v1.0.0
    git push origin v1.0.0
    echo "✅ Tag v1.0.0 created and pushed"
fi

# Step 5: Create GitHub Release
echo ""
echo "5️⃣ Creating GitHub Release..."
echo ""
echo "This will create a release with:"
echo "- Version: v1.0.0"
echo "- Title: Auto-Brainlift v1.0.0"
echo "- File: $DMG_FILE"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh release create v1.0.0 \
        --title "Auto-Brainlift v1.0.0" \
        --notes-file RELEASE_NOTES.md \
        "$DMG_FILE"
    
    echo ""
    echo "🎉 Success! Your release is live!"
    echo ""
    
    # Get the release URL
    REPO_NAME=$(echo $REMOTE_URL | sed 's/.*github.com[:/]\(.*\)\.git/\1/')
    echo "📎 Release URL:"
    echo "   https://github.com/$REPO_NAME/releases/tag/v1.0.0"
    echo ""
    echo "📥 Direct download link:"
    echo "   https://github.com/$REPO_NAME/releases/download/v1.0.0/$(basename $DMG_FILE)"
    echo ""
    echo "Share these links with your boss and users! 🚀"
else
    echo "Cancelled. You can create the release manually on GitHub.com"
fi 