# Cursor Rules Integration

## Overview

Auto-Brainlift now supports automatic creation and management of Cursor rules files (`.cursor/rules/*.mdc`) for your projects. This feature creates project-specific instructions that help AI assistants understand your project's context by directing them to read your Auto-Brainlift documentation.

## What are Cursor Rules?

Cursor rules are configuration files that provide AI assistants with context and instructions specific to your project. When enabled, Auto-Brainlift creates a `.cursor/rules/auto-brainlift.mdc` file that instructs AI assistants to:

- Review your latest context logs for project structure and recent changes
- Read brainlifts for developer insights and decision rationale
- Check error logs for known issues identified by multi-agent analysis
- Understand your development context from Cursor chat history

## How to Enable

1. Open Auto-Brainlift
2. Click the Settings button (gear icon)
3. Scroll to "Cursor Rules Integration"
4. Check "Enable Cursor Rules"
5. Select your preferred Rule Type:
   - **Always** (Recommended): Applied to every AI interaction in your project
   - **Auto Attached**: Applied when working on project files
   - **Manual**: Must be explicitly referenced
6. Click "Save Settings"

## How it Works

When enabled:
- A `.cursor/rules/auto-brainlift.mdc` file is created in your project
- This file instructs AI assistants to read your Auto-Brainlift documentation
- The AI will have context about your project's history, decisions, and current state
- When disabled, the rules file is automatically removed

## Benefits

1. **Contextual Assistance**: AI understands your project's history and decisions
2. **Consistent Support**: All team members get the same contextual AI assistance
3. **Automatic Updates**: Rules reference your latest documentation automatically
4. **Version Controlled**: Rules file can be committed to share with your team

## Rule Content

The generated rule file includes instructions for AI assistants to:

### Check Context Logs
- Current project structure and architecture
- Recent commits and changes
- Technical debt and TODOs
- Multi-agent analysis results
- Active development areas

### Review Brainlifts
- Decision rationale and thought process
- Challenges faced and solutions implemented
- Future plans and considerations
- Personal reflections on the code

### Reference Latest Documentation
- `context_logs/YYYY-MM-DD_HH-MM-SS_context.md`: Technical project state
- `brainlifts/YYYY-MM-DD_HH-MM-SS_brainlift.md`: Developer reflections
- `error_logs/YYYY-MM-DD_HH-MM-SS_error_log.md`: Issues found by agents

## Example Use Cases

1. **Onboarding New Developers**: AI can provide context-aware answers about project decisions
2. **Code Reviews**: AI understands the history behind architectural choices
3. **Bug Fixing**: AI knows about previously identified issues and attempted solutions
4. **Feature Development**: AI can reference past discussions and decisions

## Technical Details

- Rules are stored in `.cursor/rules/auto-brainlift.mdc`
- Uses modern Cursor `.mdc` format (not legacy `.cursorrules`)
- Automatically managed when switching projects
- Integrates with existing Auto-Brainlift workflow

## Troubleshooting

### Rules Not Being Applied
1. Ensure the feature is enabled in settings
2. Check that `.cursor/rules/auto-brainlift.mdc` exists in your project
3. Restart Cursor IDE after enabling the feature
4. For "Auto Attached" mode, ensure you're working on project files

### Rules File Missing
- The file is created/removed automatically based on your settings
- Check your settings to ensure the feature is enabled
- Try toggling the feature off and on again

## Privacy & Security

- Rules files only reference local documentation
- No sensitive data is included in the rules
- Rules can be excluded from version control if desired
- All AI interactions remain subject to your Cursor privacy settings 