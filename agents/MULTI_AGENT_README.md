# Multi-Agent System Documentation

## Overview

The Auto-Brainlift multi-agent system provides specialized code analysis capabilities through independent agents that can be enabled/disabled based on user needs and budget constraints.

## Architecture

### Base Agent Framework
- **base_agent.py**: Abstract base classes for all agents
  - `BaseAgent`: Core agent interface
  - `SpecializedAgent`: Common functionality for LLM-based agents
  - `AgentState`: Shared state management

### Specialized Agents

1. **Security Agent** (`security_agent.py`)
   - Analyzes code for security vulnerabilities
   - Uses pattern matching + LLM analysis
   - Detects: hardcoded secrets, SQL injection, XSS, insecure configs

2. **Code Quality Agent** (`quality_agent.py`)
   - Analyzes code complexity and maintainability
   - Metrics: cyclomatic complexity, code duplication, naming conventions
   - Provides improvement suggestions

3. **Documentation Agent** (`documentation_agent.py`)
   - Evaluates documentation coverage
   - Generates documentation suggestions
   - Analyzes: docstrings, comments, README completeness

### Agent Orchestrator
- **agent_orchestrator.py**: Manages multi-agent execution
- Execution modes:
  - **Parallel**: Run all agents simultaneously (fastest)
  - **Sequential**: Pass state between agents
  - **Priority**: Execute based on priority settings

## Configuration

### Environment Variables
The system reads agent settings from environment variables:

```bash
# Execution mode
AGENT_EXECUTION_MODE=parallel  # parallel|sequential|priority

# Security Agent
SECURITY_AGENT_ENABLED=true
SECURITY_AGENT_MODEL=gpt-4-turbo

# Quality Agent  
QUALITY_AGENT_ENABLED=true
QUALITY_AGENT_MODEL=gpt-3.5-turbo

# Documentation Agent
DOCUMENTATION_AGENT_ENABLED=false
DOCUMENTATION_AGENT_MODEL=gpt-4-turbo
```

### UI Configuration
Users can configure agents through the Settings modal:
- Toggle agents on/off
- Select models (GPT-4 Turbo or GPT-3.5 Turbo)
- Choose execution mode
- Preview estimated costs

## Integration

### Electron → Python
The Electron main process passes agent settings via environment variables when spawning the Python process:

```javascript
env: {
  ...process.env,
  AGENT_EXECUTION_MODE: settings.agentExecutionMode,
  SECURITY_AGENT_ENABLED: settings.agents.security.enabled,
  // ... other settings
}
```

### LangGraph Integration
The multi-agent system is integrated into the LangGraph workflow:
1. `_init_agent_orchestrator()` initializes the orchestrator with settings
2. `run_multi_agents` node executes agent analysis
3. Results are included in the final summaries

## Usage

### Testing
Run the test script to verify integration:
```bash
python test_multi_agent.py
```

### Manual Testing
1. Open the Auto-Brainlift app
2. Go to Settings → Multi-Agent Configuration
3. Enable/disable agents as needed
4. Save settings
5. Generate a summary - agents will run based on configuration

## Cost Management

### Token Usage
- Each agent uses approximately 1000 tokens per analysis
- Cost varies by model:
  - GPT-4 Turbo: $0.01/1k tokens
  - GPT-3.5 Turbo: $0.0015/1k tokens

### Budget Integration
- Agent token usage counts toward per-commit budget
- If budget is exceeded, agents may be skipped
- Cost preview shows estimated total cost

## Caching

Agent results are cached using the existing cache system:
- Cache key includes commit hash + agent configuration
- Results cached for 24 hours
- Cache hit skips agent execution entirely

## Error Handling

- Each agent runs independently
- One agent failure doesn't affect others
- Errors are logged but don't break the workflow
- Failed agents return error state in results

## Future Enhancements

1. **Custom Agents**: Allow users to create custom agents
2. **Agent Chaining**: Define dependencies between agents
3. **Result Aggregation**: More sophisticated result merging
4. **Custom Prompts**: User-editable agent prompts
5. **Performance Metrics**: Track agent performance over time 