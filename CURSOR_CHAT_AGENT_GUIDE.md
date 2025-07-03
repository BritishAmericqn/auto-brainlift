# Cursor Chat Agent Guide

## Overview

The Cursor Chat Agent is a specialized multi-agent component that analyzes your Cursor IDE chat conversations to extract development context, decisions, and insights. Unlike the previous inline processing, chat analysis is now handled as a proper agent within the multi-agent pipeline, providing structured analysis that other agents and summaries can build upon.

## Key Features

- **Dedicated Agent**: Chat analysis runs as part of the multi-agent system with its own enable/disable toggle and model selection
- **Structured Analysis**: Provides scores, categorized insights, and actionable summaries
- **Integration with Workflow**: Analysis happens before summary generation, allowing summaries to build on chat insights
- **Model Flexibility**: Choose between GPT-4 Turbo or GPT-3.5 Turbo based on your needs and budget

## Configuration

### Enable the Cursor Chat Agent

1. Open Auto-Brainlift
2. Click the Settings button (⚙️)
3. Navigate to **Multi-Agent Configuration**
4. Find **Cursor Chat Agent** section
5. Check "Enable Cursor chat analysis agent"
6. Select your preferred model

### Additional Settings

Under **Cursor Chat Integration** section:
- **Allow Cursor Chat Agent to read chat history**: Must be enabled for the agent to access chat data
- **Cursor Data Path**: Leave empty for auto-detection or specify custom path
- **Processing Mode**: 
  - **Light** (default): Analyzes chats since last commit
  - **Full**: Analyzes up to 7 days of history

## How It Works

### 1. Agent Pipeline Integration

The Cursor Chat Agent runs as part of the multi-agent pipeline in this order:
```
parse_git_diff → check_cache → run_multi_agents (including cursor_chat) → summarize_context → summarize_brainlift
```

### 2. Analysis Output

The agent provides structured analysis including:
- **Context Score** (0-100): How much useful context the chats provide
- **Key Decisions**: Important technical decisions made
- **Problems Solved**: Issues discussed and their resolutions
- **Implementation Guidance**: Specific implementation details
- **Learning Points**: What was learned or clarified
- **Unresolved Questions**: Outstanding issues

### 3. Integration with Summaries

The cursor chat analysis is automatically integrated into:
- **Context logs**: Shows chat analysis metrics and counts
- **Brainlifts**: Narrative insights about the development process
- **Error logs**: Highlights unresolved questions and key decisions

## Example Output

### In Context Log:
```markdown
### Cursor Chat Analysis:
- Context Score: 85/100
- Found 3 key decisions
- Solved 2 problems
- Summary: Extensive discussion about authentication implementation...
```

### In Brainlift:
```markdown
**Development Context:** The Cursor chat history reveals 3 important decisions were made. 
2 problems were discussed and resolved. This provides valuable context for understanding 
the development process.
```

## Best Practices

1. **Enable for Complex Features**: The agent is most valuable when working on complex features with extensive chat discussions
2. **Light Mode for Most Cases**: Light mode (analyzing since last commit) is usually sufficient and faster
3. **Model Selection**: 
   - Use GPT-4 Turbo for critical projects requiring deep analysis
   - Use GPT-3.5 Turbo for routine analysis to save costs
4. **Privacy**: The agent only runs when explicitly enabled - your chats remain private by default

## Cost Considerations

- **Average tokens per analysis**: ~1000 tokens
- **GPT-4 Turbo**: $0.01 per 1k tokens
- **GPT-3.5 Turbo**: $0.0015 per 1k tokens
- Chat analysis counts toward your per-commit token budget

## Troubleshooting

### Agent Not Finding Chats
1. Ensure "Allow Cursor Chat Agent to read chat history" is enabled
2. Verify Cursor is installed and has been used for the project
3. Check that you have recent chat conversations

### High Token Usage
- Switch to Light mode to only analyze recent chats
- Consider using GPT-3.5 Turbo for routine analysis
- Disable the agent for commits without significant chat context

### Integration Issues
- Clear Python cache: `find . -name "__pycache__" -type d | xargs rm -rf`
- Check logs at `logs/electron.log` for detailed error messages
- Ensure virtual environment is active

## Technical Details

The Cursor Chat Agent:
- Extends the `SpecializedAgent` base class
- Uses the existing `CursorChatReader` for database access
- Integrates with `AgentOrchestrator` for parallel/sequential execution
- Caches results with other agent outputs

## Migration from Previous Version

If you were using the previous Cursor chat integration:
1. Your settings are preserved
2. The feature now requires enabling both:
   - "Allow Cursor Chat Agent to read chat history" (under Cursor Chat Integration)
   - "Enable Cursor chat analysis agent" (under Multi-Agent Configuration)
3. Chat summaries are now part of agent results rather than appended to prompts

## Future Enhancements

Planned improvements:
- Conversation threading analysis
- Code snippet extraction from chats
- Integration with other IDE chat systems
- Custom insight categories 