#!/bin/bash
# Setup script for Auto-Brainlift Git hook

echo "🧠 Auto-Brainlift Git Hook Setup"
echo "================================"

# Check if we're in a Git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a Git repository!"
    echo "Please run this script from the root of your Git project."
    exit 1
fi

# Check if hook already exists
if [ -f ".git/hooks/post-commit" ]; then
    echo "⚠️  A post-commit hook already exists!"
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 1
    fi
    # Backup existing hook
    cp .git/hooks/post-commit .git/hooks/post-commit.backup
    echo "✅ Backed up existing hook to .git/hooks/post-commit.backup"
fi

# Create the hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-Brainlift post-commit hook
# This hook is triggered after every successful commit

# Get the directory of this script (should be .git/hooks)
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# Get the repository root (two levels up from .git/hooks)
REPO_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

# Log file for debugging
LOG_FILE="$REPO_ROOT/logs/git_hook.log"
mkdir -p "$REPO_ROOT/logs"

echo "[$(date)] Post-commit hook triggered" >> "$LOG_FILE"

# Check if Python virtual environment exists
if [ -f "$REPO_ROOT/venv/bin/python" ]; then
    PYTHON_CMD="$REPO_ROOT/venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Run the Git hook handler in the background
# This way the commit completes immediately
(
    cd "$REPO_ROOT"
    $PYTHON_CMD "$REPO_ROOT/agents/git_hook_handler.py" >> "$LOG_FILE" 2>&1 &
    echo "[$(date)] Triggered background summary generation" >> "$LOG_FILE"
) &

# Exit successfully so the commit isn't blocked
exit 0
EOF

# Make it executable
chmod +x .git/hooks/post-commit

echo "✅ Git hook installed successfully!"
echo ""
echo "The hook will automatically generate summaries after each commit."
echo ""
echo "To skip summarization for a specific commit, include one of these in your commit message:"
echo "  - [skip-brainlift]"
echo "  - [skip brainlift]"
echo "  - Start with 'WIP:'"
echo ""
echo "To disable the hook temporarily, set GIT_HOOK_ENABLED=false in your .env file."
echo ""
echo "Happy coding! 🚀" 