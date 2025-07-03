#!/bin/bash
# Setup script for Auto-Brainlift Pre-Push Git hook

echo "🚀 Auto-Brainlift Pre-Push Hook Setup"
echo "====================================="

# Check if we're in a Git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a Git repository!"
    echo "Please run this script from the root of your Git project."
    exit 1
fi

# Check if hook already exists
if [ -f ".git/hooks/pre-push" ]; then
    echo "⚠️  A pre-push hook already exists!"
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 1
    fi
    # Backup existing hook
    cp .git/hooks/pre-push .git/hooks/pre-push.backup
    echo "✅ Backed up existing hook to .git/hooks/pre-push.backup"
fi

# Create the pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Auto-Brainlift pre-push hook
# This hook is triggered before pushing commits to remote

# Get the directory of this script (should be .git/hooks)
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# Get the repository root (two levels up from .git/hooks)
REPO_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

# Log file for debugging
LOG_FILE="$REPO_ROOT/logs/git_hook.log"
mkdir -p "$REPO_ROOT/logs"

echo "[$(date)] Pre-push hook triggered" >> "$LOG_FILE"

# Check if Python virtual environment exists
if [ -f "$REPO_ROOT/venv/bin/python" ]; then
    PYTHON_CMD="$REPO_ROOT/venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Read stdin to get push information
while read local_ref local_sha remote_ref remote_sha
do
    echo "[$(date)] Pushing $local_ref to $remote_ref" >> "$LOG_FILE"
    
    # Get the branch name
    BRANCH_NAME=$(echo "$local_ref" | sed 's/refs\/heads\///')
    
    # Get commit count being pushed
    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch
        COMMIT_COUNT=$(git rev-list "$local_sha" --count)
    else
        # Existing branch
        COMMIT_COUNT=$(git rev-list "$remote_sha..$local_sha" --count)
    fi
    
    # Run the push notification handler
    (
        cd "$REPO_ROOT"
        export PUSH_BRANCH="$BRANCH_NAME"
        export PUSH_COMMITS="$COMMIT_COUNT"
        export PUSH_REMOTE="$1"  # Remote name from git push command
        export PUSH_LOCAL_SHA="$local_sha"
        export PUSH_REMOTE_SHA="$remote_sha"
        
        $PYTHON_CMD "$REPO_ROOT/agents/push_notification_handler.py" >> "$LOG_FILE" 2>&1
        echo "[$(date)] Push notification handler completed" >> "$LOG_FILE"
    ) &
done

# Exit successfully so the push isn't blocked
exit 0
EOF

# Make it executable
chmod +x .git/hooks/pre-push

echo "✅ Pre-push hook installed successfully!"
echo ""
echo "The hook will automatically send Slack notifications when you push code."
echo ""
echo "To disable the hook temporarily, set GIT_HOOK_ENABLED=false in your .env file."
echo ""
echo "Happy pushing! 🚀" 