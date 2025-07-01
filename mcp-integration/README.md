# Auto-Brainlift MCP Integration for Cursor

This directory contains the MCP (Model Context Protocol) server implementation that allows Cursor to interact with Auto-Brainlift functionality.

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI assistants like Cursor to interact with external tools and services. It's one of the few official ways to extend Cursor's functionality.

## Setup Instructions

### 1. Install Dependencies

First, ensure you have the required Node.js dependencies:

```bash
cd auto-brainlift
npm install express
```

### 2. Start the MCP Server

Run the MCP server:

```bash
node mcp-integration/mcp-server.js
```

You should see:
```
Auto-Brainlift MCP Server running on http://localhost:7734
```

### 3. Configure Cursor

Add the MCP server to your Cursor settings:

1. Open Cursor Settings (`Cmd/Ctrl + ,`)
2. Navigate to "MCP" settings
3. Add the following configuration:

```json
{
  "mcpServers": {
    "auto-brainlift": {
      "type": "http",
      "url": "http://localhost:7734"
    }
  }
}
```

4. Restart Cursor for the changes to take effect

## Available MCP Tools

Once configured, you can use these tools in Cursor's chat:

### 1. `generate_summary`
Generates AI-powered summaries for Git commits.

Example usage in Cursor chat:
```
Use the auto-brainlift tool to generate a summary for my latest commit
```

Parameters:
- `project_path` (optional): Path to the project
- `commit_hash` (optional): Specific commit to summarize

### 2. `get_project_status`
Check Auto-Brainlift status for a project.

Example usage:
```
Check the auto-brainlift status for this project
```

### 3. `list_issues` (Future Feature)
Will list detected security and quality issues once those agents are implemented.

## Example Workflows

### Workflow 1: Generate Summary After Complex Changes
```
1. Make your code changes
2. Commit your changes
3. In Cursor chat: "Generate an auto-brainlift summary for my latest commit"
4. The AI will use the MCP tool to generate summaries
```

### Workflow 2: Check Project Setup
```
1. Open a project in Cursor
2. In chat: "Is auto-brainlift set up for this project?"
3. The AI will check and report the status
```

## Troubleshooting

### MCP Server Not Found
- Ensure the server is running (`node mcp-integration/mcp-server.js`)
- Check that the port 7734 is not in use
- Verify the MCP configuration in Cursor settings

### Tool Not Working
- Restart Cursor after adding the MCP configuration
- Check the server logs for error messages
- Ensure your OPENAI_API_KEY is set in the environment

### Summary Generation Fails
- Verify Python environment is set up correctly
- Check that the project has a Git repository
- Ensure there are commits to summarize

## Advanced Configuration

### Running on a Different Port

```javascript
const server = new AutoBrainliftMCPServer(8080);
server.start();
```

Update Cursor configuration accordingly:
```json
{
  "auto-brainlift": {
    "type": "http",
    "url": "http://localhost:8080"
  }
}
```

### Running as a Background Service

For convenience, you can run the MCP server as a background service:

**macOS/Linux:**
```bash
nohup node mcp-integration/mcp-server.js > mcp-server.log 2>&1 &
```

**Windows:**
```powershell
Start-Process -WindowStyle Hidden node "mcp-integration/mcp-server.js"
```

## Limitations

- Cannot add buttons or UI elements to Cursor
- Cannot directly modify Cursor's interface
- Requires manual server startup (for now)
- Tools are invoked through chat, not automatically

## Future Enhancements

- Auto-start with Cursor
- WebSocket support for real-time updates
- Integration with security and quality agents
- Batch operations support 