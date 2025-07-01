# Auto-Brainlift Project Summary

## What We Built
Auto-Brainlift is a desktop application that automatically generates AI-powered development summaries after every Git commit. It creates two types of documentation:
- **context.md**: Technical summaries for AI coding assistants
- **brainlift.md**: Personal reflective journal entries

## Architecture Overview
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Git Commit    │────▶│   Git Hook      │────▶│  Python Agent   │
│                 │     │ (post-commit)   │     │  (LangGraph)    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────┐               │
                        │  Electron UI    │◀──────────────┘
                        │  (Manual Gen)   │               │
                        └─────────────────┘               ▼
                                                 ┌─────────────────┐
                                                 │   OpenAI API    │
                                                 └────────┬────────┘
                                                          │
                                    ┌─────────────────────┴─────────────────────┐
                                    ▼                                           ▼
                           ┌─────────────────┐                         ┌─────────────────┐
                           │  context_logs/  │                         │   brainlifts/   │
                           │   context.md    │                         │  brainlift.md   │
                           └─────────────────┘                         └─────────────────┘
```

## Key Components

### 1. Electron Desktop App (`/electron/`, `index.html`)
- Vanilla HTML/JS interface (no React)
- Manual "Generate Summary" button
- Real-time display of generated summaries
- Skeleton loaders and micro-interactions
- IPC communication with main process

### 2. Python LangGraph Agent (`/agents/langgraph_agent.py`)
- Linear workflow: parse_git_diff → summarize_context → summarize_brainlift → write_output
- Uses OpenAI GPT-4 for generation
- Handles both manual and automatic triggers
- Comprehensive error logging

### 3. Git Integration (`/agents/git_hook_handler.py`)
- Post-commit hook triggers automatically
- Tracks processed commits to avoid duplicates
- Skip keywords: [skip-brainlift], WIP:, merge
- Non-blocking background processing

### 4. Retry System (`/agents/retry_manager.py`)
- Exponential backoff for failed API calls
- Maximum 3 retry attempts
- Persistent retry queue
- Optional cron job for automatic retries

## Setup Commands
```bash
# Install dependencies
npm install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.template .env
# Add OpenAI API key to .env

# Install Git hook
./setup_git_hook.sh

# Optional: Setup retry cron
./setup_retry_cron.sh

# Run desktop app
npm start
```

## File Structure
```
auto-brainlift/
├── agents/              # Python backend
├── brainlifts/         # Generated reflections
├── context_logs/       # Generated context
├── electron/           # Electron main process
├── logs/              # Debug logs
├── prompts/           # AI templates
├── .env               # Configuration
├── index.html         # UI
└── package.json       # Node deps
```

## Future Ideas
- Support for other AI providers (Claude, local models)
- Integration with VS Code extension
- Team sharing features
- Summary search and tagging
- Export to Markdown blog posts
- Integration with other version control systems

## Lessons Learned
- Vanilla HTML/JS can be simpler than React for small apps
- Linear LangGraph flows are easier to debug
- Background processing is crucial for Git hooks
- Good logging saves debugging time
- AI-generated documentation can be surprisingly insightful

---

Built with ❤️ to help developers remember their coding journey. 