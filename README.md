# 🧠 Auto-Brainlift

Automatically generate AI-powered development summaries after every Git commit. Auto-Brainlift creates two types of documentation:
- **context.md**: Technical, structured summaries for AI coding assistants
- **brainlift.md**: Personal, reflective journal entries about your coding journey

## Features

- 🔄 **Automatic Generation**: Summaries created automatically after each Git commit
- 🎯 **Dual Output**: Technical context for AI + personal reflections for developers
- 🖥️ **Desktop App**: Clean Electron UI for manual generation and viewing
- 🔁 **Retry Logic**: Automatic retry with exponential backoff for failed generations
- 🏃 **Background Processing**: Git commits complete immediately, summaries generate async
- 🎨 **Clean UI**: Skeleton loaders, micro-interactions, and modern design

## Quick Start

### Prerequisites
- macOS (tested on 11.0+)
- Node.js 16+
- Python 3.8+
- Git
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/auto-brainlift.git
   cd auto-brainlift
   ```

2. **Install Node dependencies**
   ```bash
   npm install
   ```

3. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

4. **Configure OpenAI API**
   ```bash
   cp .env.template .env
   # Edit .env and add your OpenAI API key
   ```

5. **Install Git hook (optional)**
   ```bash
   ./setup_git_hook.sh
   ```

6. **Set up retry cron job (optional)**
   ```bash
   ./setup_retry_cron.sh
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
│   ├── langgraph_agent.py    # Main summarization agent
│   ├── git_hook_handler.py   # Git hook integration
│   └── retry_manager.py      # Retry queue management
├── brainlifts/         # Personal reflection outputs
├── context_logs/       # AI context outputs
├── electron/           # Electron main process
├── logs/              # Application logs
├── prompts/           # AI prompt templates
│   ├── context.txt    # Template for technical summaries
│   └── brainlift.txt  # Template for reflective entries
├── ui/                # UI components
├── .env               # Environment configuration
├── index.html         # Main UI (vanilla HTML/JS)
└── package.json       # Node dependencies
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Electron](https://www.electronjs.org/)
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph)
- AI by [OpenAI](https://openai.com/)

---

Made with ❤️ for developers who want to remember their coding journey
