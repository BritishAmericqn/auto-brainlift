# Auto-Brainlift Slack Integration Guide

Auto-Brainlift now includes enhanced Slack integration with both manual and automated notifications to keep your team updated on development progress.

## Features

### 1. Manual Progress Updates ("Send to Slack" Button)
Send on-demand progress updates to Slack regardless of commit status:
- **Current Work**: What you're actively working on
- **Progress Made**: Recent accomplishments
- **Code Changes**: Modified files and features
- **Issues & Blockers**: Any problems encountered
- **Git Status**: Branch, commit status, and change statistics

### 2. Automated Notifications
- **Post-Commit**: Automatic brainlift summaries after commits (existing feature)
- **Pre-Push**: Notifications when pushing code to remote repositories (new)

## Setup Instructions

### 1. Configure Slack Integration

1. **Create a Slack App**:
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App"
   - Choose "From scratch"
   - Name your app (e.g., "Auto-Brainlift")
   - Select your workspace

2. **Set Bot Permissions**:
   - Navigate to "OAuth & Permissions"
   - Add these scopes:
     - `chat:write`
     - `chat:write.public` (to post to public channels)
   - Install the app to your workspace
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

3. **Configure in Auto-Brainlift**:
   - Open Settings (⚙️)
   - Enable "Slack Integration"
   - Paste your bot token
   - Enter your channel (e.g., `#dev-updates`)
   - Test the connection

### 2. Set Up Git Hooks for Automated Notifications

**For Push Notifications**:
```bash
# From your project root
./auto-brainlift/setup_pre_push_hook.sh
```

This installs a pre-push hook that sends notifications when you push code.

## Usage

### Manual Progress Updates

1. Click the **"📨 Send to Slack"** button in the main interface
2. Auto-Brainlift will gather:
   - Current git status and changes
   - Recent commits
   - Work context from your latest brainlifts
   - Any logged issues
3. A formatted update is sent to your configured Slack channel

### Message Format

**Progress Updates** include:
```
📊 Progress Update: [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Currently Working On:
• Feature implementation...
• Bug fixes...

Progress Made:
✅ Completed authentication flow
✅ Fixed database connection issues

Code Changes & Features:
• Modified: components/Auth.tsx
• Added: utils/validation.js

Issues & Blockers:
⚠️ API rate limiting causing delays

Status: ⏳ Uncommitted Changes | Branch: feature/auth
Files Changed: 5 | Lines Added: +120 / -45
```

**Push Notifications** include:
```
🚀 Code Push: [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Branch: main | Commits: 3
Pushed to: origin

Recent Commits:
• `a1b2c3d` Fix authentication bug
• `e4f5g6h` Add user validation
• `i7j8k9l` Update documentation

Files Changed: 8 | Lines: +234 / -89
```

## Notification Rules

Configure when to receive automated notifications:
- **All**: Every brainlift and push
- **Issues Only**: Only when issues are detected
- **Critical Only**: Only when scores fall below 70

## Best Practices

1. **Regular Updates**: Use "Send to Slack" periodically during long coding sessions
2. **Meaningful Commits**: Write clear commit messages for better push notifications
3. **Team Communication**: Include context about blockers or help needed
4. **Channel Selection**: Use project-specific channels for focused updates

## Troubleshooting

**Slack not working?**
1. Check bot token is correct (starts with `xoxb-`)
2. Ensure bot is added to the channel
3. Test connection in Settings
4. Check logs at `~/Library/Application Support/auto-brainlift/logs/`

**Push notifications not sending?**
1. Verify pre-push hook is installed: `ls -la .git/hooks/pre-push`
2. Check if Slack is enabled in Settings
3. View push notification logs: `tail -f ~/Library/Application Support/auto-brainlift/logs/push_notifications.log`

**To disable temporarily**:
- Set `GIT_HOOK_ENABLED=false` in your `.env` file
- Or disable Slack integration in Settings

## Privacy & Security

- Bot tokens are stored locally in your system's app data directory
- No data is sent to Slack without your explicit action
- Git hooks run locally and can be disabled at any time
- All notifications respect your configured channel settings 