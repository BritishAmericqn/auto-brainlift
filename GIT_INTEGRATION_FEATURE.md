# Git Integration Feature for Auto-Brainlift

## Overview

Auto-Brainlift now includes a feature to control whether generated files (brainlifts, context logs, and error logs) are tracked by Git. This allows you to decide whether these files should be included when you commit and push to your repository.

## How It Works

1. **Toggle Setting**: In the Settings modal, under "Git Integration", you'll find a toggle for "Include brainlift and context files in git commits"
   
2. **Default Behavior**: By default, this feature is **disabled**, meaning generated files are listed in `.gitignore` and won't be committed
   
3. **When Enabled**: 
   - The directories `brainlifts/`, `context_logs/`, and `error_logs/` are removed from `.gitignore`
   - Generated files will be tracked by Git
   - When you commit and push, these files will be included

4. **When Disabled**: 
   - The directories are added to `.gitignore`
   - Generated files remain local only
   - Git will ignore these files when you commit

## Configuration

### Enabling/Disabling Git Tracking

1. Click the "Settings" button in the Auto-Brainlift UI
2. Navigate to the "Git Integration" section
3. Toggle "Include brainlift and context files in git commits"
4. Click "Save Settings"

The `.gitignore` file in your project will be automatically updated based on your choice.

## Use Cases

### When to Enable Git Tracking
- **Team collaboration**: Share development insights with your team
- **Documentation**: Maintain a history of project evolution in your repository
- **Remote backup**: Keep summaries backed up on GitHub/GitLab/etc
- **Open source**: Share your development process with the community

### When to Keep Disabled
- **Private/sensitive projects**: Keep insights local
- **Proprietary codebases**: Avoid exposing internal details
- **Repository cleanliness**: Prevent generated files from cluttering the repo
- **Review before sharing**: Manually choose which summaries to commit

## Manual Control

Even with Git tracking disabled, you can still manually commit specific files:

```bash
# Force add specific files (overrides .gitignore)
git add -f brainlifts/2024-01-15_summary.md
git commit -m "Add important development summary"
git push
```

Or temporarily include all generated files:

```bash
# Force add all generated files
git add -f brainlifts/*.md context_logs/*.md error_logs/*.md
git commit -m "Add development summaries"
git push
```

## What Gets Modified

When you toggle the setting, Auto-Brainlift modifies your project's `.gitignore` file:

**When disabled (default):**
```gitignore
# Auto-Brainlift generated files
brainlifts/
context_logs/
error_logs/
```

**When enabled:**
These lines are removed from `.gitignore`, allowing Git to track the files.

## Security Considerations

- Generated summaries may contain code snippets and architectural details
- Review the content of generated files before enabling Git tracking
- Consider using private repositories for sensitive projects
- Once pushed, these files become part of your repository history

## Troubleshooting

If files aren't being tracked as expected:
1. Check your `.gitignore` file to verify the patterns are correctly added/removed
2. Use `git status` to see if files are being ignored
3. Try `git add -f` to force-add files if needed
4. Ensure you've saved the settings in the Auto-Brainlift UI 