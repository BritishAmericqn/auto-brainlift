#!/bin/bash
# Setup cron job for Auto-Brainlift retry queue

echo "🔄 Auto-Brainlift Retry Queue Setup"
echo "==================================="

# Get the absolute path to the project
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if Python virtual environment exists
if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_DIR/venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Create the cron command
CRON_CMD="*/15 * * * * cd $PROJECT_DIR && $PYTHON_CMD $PROJECT_DIR/agents/retry_manager.py >> $PROJECT_DIR/logs/retry_cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "retry_manager.py"; then
    echo "⚠️  A retry cron job already exists!"
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 1
    fi
    # Remove existing cron job
    crontab -l | grep -v "retry_manager.py" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Cron job installed successfully!"
echo ""
echo "The retry queue will be processed every 15 minutes."
echo ""
echo "To view the cron job:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -l | grep -v 'retry_manager.py' | crontab -"
echo ""
echo "To view retry logs:"
echo "  tail -f $PROJECT_DIR/logs/retry_cron.log" 