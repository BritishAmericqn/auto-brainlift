# 🧠 Auto-Brainlift

[![Latest Release](https://img.shields.io/github/v/release/benjaminroyston/auto-brainlift)](https://github.com/benjaminroyston/auto-brainlift/releases)
[![Downloads](https://img.shields.io/github/downloads/benjaminroyston/auto-brainlift/total)](https://github.com/benjaminroyston/auto-brainlift/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Automatically generate AI-powered development summaries after every Git commit. Auto-Brainlift creates two types of documentation:
- **context.md**: Technical, structured summaries for AI coding assistants
- **brainlift.md**: Personal, reflective journal entries about your coding journey

## 🎉 Phase 2 Complete: Smart Caching System

Auto-Brainlift now includes intelligent caching to reduce API costs by up to 10x! Features include:
- 🚀 Multi-tier caching (exact match → semantic → full LLM)
- 💰 Budget management with per-commit token limits
- 📊 Real-time cache performance and cost analytics

See [PHASE2_CACHING_GUIDE.md](PHASE2_CACHING_GUIDE.md) for full details.

## ✨ Features

- 🚀 **Automatic Documentation**: Generates context and reflection files after each commit
- 🧠 **Multi-Agent Analysis**: Security, quality, and documentation agents review your code
- 💾 **Smart Caching**: 3-tier caching system reduces API costs by ~65%
- 💰 **Budget Management**: Set token limits and track costs per commit
- 📊 **Beautiful UI**: Electron-based interface with real-time updates
- 🔍 **Git Integration**: Seamlessly hooks into your Git workflow
- 💬 **Cursor Chat Integration**: Optionally analyze development context from Cursor chats (Beta)
- 📋 **Cursor Rules Integration**: Auto-create rules files for AI-aware assistance (New!)
- 🌐 **MCP Integration**: Use Auto-Brainlift directly in Claude Desktop
- 🤖 **Multi-Agent System**: Parallel analysis by specialized agents
- 🎯 **Flexible Agent Execution**: Sequential, parallel, or priority-based processing
- 📝 **Error Tracking**: Comprehensive error_log.md with categorized issues
- 🚦 **Retry Mechanisms**: Automatic retry with exponential backoff
- 💻 **Cross-Platform**: Windows, macOS, and Linux support
- 🔄 **Project Management**: Handle multiple projects with isolated settings
- 📊 **Analytics Dashboard**: Real-time cache performance and cost metrics
- 🔐 **Project Isolation**: Complete data separation between projects

## 🚀 Quick Start

### Download & Install (Recommended)

#### macOS
1. Download the latest `.dmg` from [Releases](https://github.com/benjaminroyston/auto-brainlift/releases)
2. Double-click to mount the DMG
3. Drag Auto-Brainlift to your Applications folder
4. **First Launch**: Right-click the app → Open (to bypass Gatekeeper)

#### Windows
1. Download the latest `.exe` installer from [Releases](https://github.com/benjaminroyston/auto-brainlift/releases)
2. Run the installer
3. Follow the installation wizard

#### Linux
1. Download the latest `.AppImage` from [Releases](https://github.com/benjaminroyston/auto-brainlift/releases)
2. Make it executable: `chmod +x Auto-Brainlift-*.AppImage`
3. Run: `./Auto-Brainlift-*.AppImage`

### System Requirements
- **Python 3.8+** must be installed on your system
- **OpenAI API Key** (get one at [platform.openai.com](https://platform.openai.com))

### Development Setup

If you want to run from source:

1. **Clone the repository**
   ```bash
   git clone https://github.com/benjaminroyston/auto-brainlift.git
   cd auto-brainlift
   ```

2. **Install dependencies**
   ```bash
   npm install
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

3. **Run in development mode**
   ```bash
   npm start
   ```

## Usage

### Desktop App
```bash
npm start
```
- Click "Generate Summary" to manually process the latest commit
- View generated summaries in the two panels
- Use Cmd/Ctrl+G keyboard shortcut for quick access

### Git Hook (Automatic)
Once installed, summaries are generated automatically after each commit:
```bash
git add .
git commit -m "Your commit message"
# Summaries generate in background
```

### Skip Summary Generation
Add these keywords to your commit message to skip generation:
- `[skip-brainlift]` or `[skip brainlift]`
- Start message with `WIP:`
- Merge commits are skipped automatically

### Manual Testing
```bash
source venv/bin/activate
python test_agent.py
```

## Project Structure

```
auto-brainlift/
├── agents/              # Python LangGraph logic
│   ├── cache/          # Caching system (NEW)
│   │   ├── cache_manager.py
│   │   ├── exact_cache.py
│   │   └── semantic_cache.py
│   ├── langgraph_agent.py    # Main summarization agent
│   ├── cursor_chat_reader.py # Cursor chat integration (NEW)
│   ├── git_hook_handler.py   # Git hook integration
│   ├── retry_manager.py      # Retry queue management
│   └── budget_manager.py     # Token budget tracking (NEW)
├── brainlifts/         # Personal reflection outputs
├── context_logs/       # AI context outputs
├── electron/           # Electron main process
│   └── projectManager.js     # Multi-project support (NEW)
├── logs/              # Application logs
├── mcp-integration/    # Cursor IDE integration
│   ├── mcp-server.js  # MCP server for Cursor
│   └── README.md      # MCP setup instructions
├── prompts/           # AI prompt templates
│   ├── context.txt    # Template for technical summaries
│   └── brainlift.txt  # Template for reflective entries
├── ui/                # UI components
├── .env               # Environment configuration
├── index.html         # Main UI (vanilla HTML/JS)
├── package.json       # Node dependencies
├── EXPANSION_PLAN.md  # Roadmap for new features
├── PITFALLS_TO_AVOID.md # Common mistakes guide
├── PHASE2_CACHING_GUIDE.md # Caching system docs (NEW)
└── test_cache.py      # Cache testing script (NEW)
```

## Configuration

### Environment Variables (.env)
```bash
# AI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=30

# Output Directories
OUTPUT_DIR=./brainlifts
CONTEXT_DIR=./context_logs

# Features
GIT_HOOK_ENABLED=true
SKIP_EXISTING_COMMITS=true

# Budget Management (NEW)
BUDGET_ENABLED=false
COMMIT_TOKEN_LIMIT=10000

# Cursor Chat Integration (Beta)
CURSOR_CHAT_ENABLED=false
CURSOR_CHAT_PATH=  # Leave empty for auto-detection
CURSOR_CHAT_MODE=light  # Options: light (default), full
CURSOR_CHAT_INCLUDE_IN_SUMMARY=true  # Set to false to save tokens

# Git Integration (managed via UI settings)
# Use the Settings modal to control whether generated files are tracked by Git
```

### Customizing Prompts
Edit the prompt templates in `/prompts/`:
- `context.txt`: Modify the structure of technical summaries
- `brainlift.txt`: Adjust the tone of personal reflections

## Architecture

### LangGraph Flow (Linear)
```
parse_git_diff → summarize_context → summarize_brainlift → write_output
```

### Technology Stack
- **Frontend**: Vanilla HTML/JS with Electron
- **Backend**: Python with LangGraph
- **AI**: OpenAI GPT-4
- **Process Management**: Node.js child_process
- **Version Control**: GitPython
- **IDE Integration**: Cursor Rules (.mdc format) for AI context awareness

## Troubleshooting

### Check Logs
```bash
# Git hook logs
tail -f logs/git_hook.log

# LangGraph agent logs
tail -f logs/langgraph_agent.log

# Electron logs
tail -f logs/electron.log

# Retry queue logs
tail -f logs/retry_cron.log
```

### Common Issues

**"No module named 'dotenv'"**
- Ensure virtual environment is activated: `source venv/bin/activate`

**Git hook not triggering**
- Check hook is executable: `ls -la .git/hooks/post-commit`
- Verify GIT_HOOK_ENABLED=true in .env

**API rate limits**
- Retry queue will automatically handle rate limits
- Check retry status: `cat .retry_queue.json`

**Summaries not appearing in UI**
- Check output directories exist
- Verify file permissions
- Check API key is valid

## Development

### Running Tests
```bash
# Test Python agent
source venv/bin/activate
python test_agent.py

# Test Git hook
./agents/git_hook_handler.py

# Test retry queue
./agents/retry_manager.py
```

### Adding New Features
1. Follow the linear LangGraph pattern
2. Add logging for debugging
3. Update prompts if needed
4. Test with manual trigger first

## 🚀 Expansion Features (Coming Soon)

### Cursor IDE Integration
Auto-Brainlift now includes experimental MCP (Model Context Protocol) integration for Cursor:

```bash
# Start MCP server
node mcp-integration/mcp-server.js

# In Cursor chat:
"Generate an auto-brainlift summary for my latest commit"
```

See [mcp-integration/README.md](mcp-integration/README.md) for setup instructions.

### Cursor Rules Integration

Auto-Brainlift can automatically create Cursor rules files that instruct AI assistants to read your project's context logs and brainlifts. This gives AI deep understanding of your project's history and decisions.

Enable in Settings > Cursor Rules Integration. See [CURSOR_RULES_INTEGRATION.md](CURSOR_RULES_INTEGRATION.md) for details.

### Cursor Chat Integration
Analyze your development conversations to provide richer context in summaries:
- Privacy-first: opt-in feature, disabled by default
- Timestamp-based: only analyzes chats between commits
- Development insights: extracts key decisions, bug fixes, and implementation notes

See [CURSOR_CHAT_INTEGRATION.md](CURSOR_CHAT_INTEGRATION.md) for setup and usage.

### Planned Features
- **Multi-Project Support**: Manage summaries across multiple repositories
- **AI Agent Orchestration**: Security scanning, code quality analysis
- **Enhanced Cursor Integration**: CLI tools, clipboard integration

For the complete roadmap, see [EXPANSION_PLAN.md](EXPANSION_PLAN.md).

## 🔨 Building from Source

### Prerequisites
- Node.js 18+
- Python 3.8+
- ImageMagick (for icon generation): `brew install imagemagick`

### Build Process

```bash
# Generate icons (first time only)
cd build && ./generate-icons.sh && cd ..

# Build for your platform
npm run build:mac    # Creates DMG for macOS
npm run build:win    # Creates EXE for Windows
npm run build:linux  # Creates AppImage for Linux

# Or use the release script
./release.sh 1.0.3  # Automates the entire process
```

Build outputs will be in the `dist/` directory. See [PRODUCTION_BUILD_GUIDE.md](PRODUCTION_BUILD_GUIDE.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Guidelines
- Read [PITFALLS_TO_AVOID.md](PITFALLS_TO_AVOID.md) before starting
- Keep the architecture simple and maintainable
- Test edge cases thoroughly
- Document any new features

### Creating a Release

1. Update version: `npm version patch`
2. Build: `./release.sh <version>`
3. Test the build locally
4. Push tags: `git push && git push origin v<version>`
5. Create GitHub release with the artifacts from `dist/`

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Electron](https://www.electronjs.org/)
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph)
- AI by [OpenAI](https://openai.com/)

---

Made with ❤️ for developers who want to remember their coding journey
// Test for Slack notification
