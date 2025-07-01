/**
 * MCP (Model Context Protocol) Server for Auto-Brainlift
 * This allows Cursor to interact with Auto-Brainlift functionality
 */

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class AutoBrainliftMCPServer {
  constructor(port = 7734) {
    this.app = express();
    this.port = port;
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    this.app.use(express.json());
    this.app.use((req, res, next) => {
      // CORS headers for MCP
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type');
      next();
    });
  }

  setupRoutes() {
    // MCP discovery endpoint
    this.app.get('/', (req, res) => {
      res.json({
        name: 'Auto-Brainlift',
        version: '1.0.0',
        description: 'AI-powered Git commit summaries',
        tools: [
          {
            name: 'generate_summary',
            description: 'Generate AI summary for the latest Git commit',
            parameters: {
              type: 'object',
              properties: {
                project_path: {
                  type: 'string',
                  description: 'Path to the project (optional, uses current directory if not provided)'
                },
                commit_hash: {
                  type: 'string',
                  description: 'Specific commit hash to summarize (optional, uses latest if not provided)'
                }
              }
            }
          },
          {
            name: 'get_project_status',
            description: 'Get Auto-Brainlift status for a project',
            parameters: {
              type: 'object',
              properties: {
                project_path: {
                  type: 'string',
                  description: 'Path to the project'
                }
              }
            }
          },
          {
            name: 'list_issues',
            description: 'List detected issues from the latest analysis',
            parameters: {
              type: 'object',
              properties: {
                project_path: {
                  type: 'string',
                  description: 'Path to the project'
                }
              }
            }
          }
        ]
      });
    });

    // Tool execution endpoint
    this.app.post('/execute', async (req, res) => {
      const { tool, parameters } = req.body;

      try {
        let result;
        switch (tool) {
          case 'generate_summary':
            result = await this.generateSummary(parameters);
            break;
          case 'get_project_status':
            result = await this.getProjectStatus(parameters);
            break;
          case 'list_issues':
            result = await this.listIssues(parameters);
            break;
          default:
            throw new Error(`Unknown tool: ${tool}`);
        }
        
        res.json({ success: true, result });
      } catch (error) {
        res.status(400).json({ 
          success: false, 
          error: error.message 
        });
      }
    });

    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ status: 'healthy', timestamp: new Date().toISOString() });
    });
  }

  async generateSummary(parameters) {
    const projectPath = parameters.project_path || process.cwd();
    const commitHash = parameters.commit_hash || 'HEAD';

    return new Promise((resolve, reject) => {
      const pythonPath = path.join(__dirname, '../venv/bin/python');
      const scriptPath = path.join(__dirname, '../agents/langgraph_agent.py');
      
      const pythonCommand = fs.existsSync(pythonPath) ? pythonPath : 'python3';
      
      const args = [scriptPath];
      if (commitHash && commitHash !== 'HEAD') {
        args.push(commitHash);
      }

      const pythonProcess = spawn(pythonCommand, args, {
        cwd: projectPath,
        env: { ...process.env }
      });

      let output = '';
      let errorOutput = '';

      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          // Parse the output to find file paths
          const contextMatch = output.match(/Context log: (.+)/);
          const brainliftMatch = output.match(/Brainlift: (.+)/);
          
          resolve({
            message: 'Summary generated successfully',
            context_file: contextMatch ? contextMatch[1] : null,
            brainlift_file: brainliftMatch ? brainliftMatch[1] : null,
            output: output
          });
        } else {
          reject(new Error(`Summary generation failed: ${errorOutput || output}`));
        }
      });
    });
  }

  async getProjectStatus(parameters) {
    const projectPath = parameters.project_path || process.cwd();
    
    // Check if Auto-Brainlift is set up for this project
    const gitHookPath = path.join(projectPath, '.git/hooks/post-commit');
    const hookExists = fs.existsSync(gitHookPath);
    
    // Get latest summary files
    const brainliftsDir = path.join(projectPath, 'brainlifts');
    const contextDir = path.join(projectPath, 'context_logs');
    
    let latestBrainlift = null;
    let latestContext = null;
    
    if (fs.existsSync(brainliftsDir)) {
      const files = fs.readdirSync(brainliftsDir)
        .filter(f => f.endsWith('.md'))
        .sort()
        .reverse();
      if (files.length > 0) {
        latestBrainlift = files[0];
      }
    }
    
    if (fs.existsSync(contextDir)) {
      const files = fs.readdirSync(contextDir)
        .filter(f => f.endsWith('.md'))
        .sort()
        .reverse();
      if (files.length > 0) {
        latestContext = files[0];
      }
    }

    return {
      project_path: projectPath,
      hook_installed: hookExists,
      latest_brainlift: latestBrainlift,
      latest_context: latestContext,
      brainlifts_count: latestBrainlift ? fs.readdirSync(brainliftsDir).length : 0,
      context_logs_count: latestContext ? fs.readdirSync(contextDir).length : 0
    };
  }

  async listIssues(parameters) {
    // This would integrate with the future security/quality agents
    // For now, return a placeholder
    return {
      message: 'Issue detection not yet implemented',
      issues: []
    };
  }

  start() {
    this.app.listen(this.port, () => {
      console.log(`Auto-Brainlift MCP Server running on http://localhost:${this.port}`);
      console.log(`Add this to your Cursor MCP configuration:`);
      console.log(JSON.stringify({
        "auto-brainlift": {
          "type": "http",
          "url": `http://localhost:${this.port}`
        }
      }, null, 2));
    });
  }
}

// Start the server if run directly
if (require.main === module) {
  const server = new AutoBrainliftMCPServer();
  server.start();
}

module.exports = AutoBrainliftMCPServer; 