# Auto-Brainlift Demo Instructions

## Quick Setup for Demo

1. **Set up API Key**:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key

2. **Build the App**:
   ```bash
   npm run build
   ```

3. **Find the Installer**:
   - Look in the `dist/` folder
   - macOS: `Auto-Brainlift-1.0.0.dmg`
   - Windows: `Auto-Brainlift Setup 1.0.0.exe`
   - Linux: `Auto-Brainlift-1.0.0.AppImage`

4. **Install and Run**:
   - Install the app like any other desktop application
   - On first run, enter your OpenAI API key when prompted

## Demo Talking Points

- **Automatic Git Integration**: Watches for commits and generates summaries
- **AI-Powered Analysis**: Uses GPT-4 to understand code changes
- **Multi-Agent System**: Security, quality, and documentation agents
- **Smart Caching**: Reduces API costs with intelligent caching
- **Project Management**: Handle multiple projects from one interface

## Known Limitations (Demo Version)

- No code signing (users will see security warnings)
- Python must be installed on the system
- Manual API key entry required
- No auto-update functionality yet

## Troubleshooting

If the app doesn't start:
1. Check that Python 3.8+ is installed
2. Verify the API key is correct
3. Check logs in: `~/Library/Application Support/auto-brainlift/logs/`
