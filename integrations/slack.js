const { WebClient } = require('@slack/web-api');
const { execSync } = require('child_process');

class SlackIntegration {
  constructor(token, options = {}) {
    this.client = new WebClient(token);
    this.defaultChannel = options.channel || '#dev-updates';
  }

  async testConnection() {
    try {
      const result = await this.client.auth.test();
      return { 
        success: true, 
        team: result.team, 
        user: result.user,
        userId: result.user_id 
      };
    } catch (error) {
      return { 
        success: false, 
        error: error.message 
      };
    }
  }

  async sendBrainliftSummary(data, projectName) {
    try {
      const blocks = this.formatBrainliftMessage(data, projectName);
      
      const result = await this.client.chat.postMessage({
        channel: this.defaultChannel,
        text: `🧠 Brainlift Summary: ${projectName}`,
        blocks: blocks
      });
      
      return { success: true, messageId: result.ts };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async sendProgressUpdate(data, projectName) {
    try {
      const blocks = this.formatProgressMessage(data, projectName);
      
      const result = await this.client.chat.postMessage({
        channel: this.defaultChannel,
        text: `📊 Progress Update: ${projectName}`,
        blocks: blocks
      });
      
      return { success: true, messageId: result.ts };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async sendPushNotification(data, projectName) {
    try {
      const blocks = this.formatPushMessage(data, projectName);
      
      const result = await this.client.chat.postMessage({
        channel: this.defaultChannel,
        text: `🚀 Code Push: ${projectName}`,
        blocks: blocks
      });
      
      return { success: true, messageId: result.ts };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  formatBrainliftMessage(data, projectName) {
    const blocks = [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: `🧠 Brainlift Summary: ${projectName}`
        }
      },
      {
        type: "divider"
      }
    ];

    // Add test message if this is a test
    if (data.isTest && data.testMessage) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: data.testMessage
        }
      });
      blocks.push({
        type: "divider"
      });
    }

    // Add scores section
    if (data.scores) {
      blocks.push({
        type: "section",
        fields: [
          {
            type: "mrkdwn",
            text: `*Overall Score:* ${data.scores.overall || 'N/A'}/100`
          },
          {
            type: "mrkdwn", 
            text: `*Security:* ${data.scores.security || 'N/A'}/100`
          },
          {
            type: "mrkdwn",
            text: `*Quality:* ${data.scores.quality || 'N/A'}/100`
          },
          {
            type: "mrkdwn",
            text: `*Documentation:* ${data.scores.documentation || 'N/A'}/100`
          }
        ]
      });
    }

    // Add commit info
    if (data.commitHash) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Commit:* \`${data.commitHash.substring(0, 8)}\`${data.commitMessage ? `\n*Message:* ${data.commitMessage}` : ''}`
        }
      });
    }

    // Add critical issues
    if (data.criticalIssues && data.criticalIssues.length > 0) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*🚨 Critical Issues (${data.criticalIssues.length}):*`
        }
      });
      
      data.criticalIssues.slice(0, 5).forEach(issue => {
        blocks.push({
          type: "section",
          text: {
            type: "mrkdwn",
            text: `• ${issue}`
          }
        });
      });
    }

    // Add timestamp
    blocks.push({
      type: "context",
      elements: [
        {
          type: "mrkdwn",
          text: `Generated: ${new Date().toLocaleString()}`
        }
      ]
    });

    return blocks;
  }

  formatProgressMessage(data, projectName) {
    const blocks = [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: `📊 Progress Update: ${projectName}`
        }
      },
      {
        type: "divider"
      }
    ];

    // Current work section
    if (data.currentWork && data.currentWork.length > 0) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: "*Currently Working On:*"
        }
      });
      
      data.currentWork.forEach(item => {
        blocks.push({
          type: "section",
          text: {
            type: "mrkdwn",
            text: `• ${item}`
          }
        });
      });
    }

    // Progress made section
    if (data.progressMade && data.progressMade.length > 0) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: "*Progress Made:*"
        }
      });
      
      data.progressMade.forEach(item => {
        blocks.push({
          type: "section",
          text: {
            type: "mrkdwn",
            text: `✅ ${item}`
          }
        });
      });
    }

    // Features/Code changes
    if (data.codeChanges && data.codeChanges.length > 0) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: "*Code Changes & Features:*"
        }
      });
      
      data.codeChanges.forEach(change => {
        blocks.push({
          type: "section",
          text: {
            type: "mrkdwn",
            text: `• ${change}`
          }
        });
      });
    }

    // Issues encountered
    if (data.issues && data.issues.length > 0) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: "*Issues & Blockers:*"
        }
      });
      
      data.issues.forEach(issue => {
        blocks.push({
          type: "section",
          text: {
            type: "mrkdwn",
            text: `⚠️ ${issue}`
          }
        });
      });
    }

    // Commit status
    blocks.push({
      type: "section",
      fields: [
        {
          type: "mrkdwn",
          text: `*Status:* ${data.hasCommitted ? '✅ Changes Committed' : '⏳ Uncommitted Changes'}`
        },
        {
          type: "mrkdwn",
          text: `*Branch:* ${data.branch || 'Unknown'}`
        }
      ]
    });

    // Git stats if available
    if (data.gitStats) {
      blocks.push({
        type: "section",
        fields: [
          {
            type: "mrkdwn",
            text: `*Files Changed:* ${data.gitStats.filesChanged || 0}`
          },
          {
            type: "mrkdwn",
            text: `*Lines Added:* +${data.gitStats.linesAdded || 0} / -${data.gitStats.linesDeleted || 0}`
          }
        ]
      });
    }

    // Timestamp
    blocks.push({
      type: "context",
      elements: [
        {
          type: "mrkdwn",
          text: `Generated: ${new Date().toLocaleString()}`
        }
      ]
    });

    return blocks;
  }

  formatPushMessage(data, projectName) {
    const blocks = [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: `🚀 Code Push: ${projectName}`
        }
      },
      {
        type: "divider"
      }
    ];

    // Branch and commit info
    blocks.push({
      type: "section",
      fields: [
        {
          type: "mrkdwn",
          text: `*Branch:* ${data.branch}`
        },
        {
          type: "mrkdwn",
          text: `*Commits:* ${data.commitCount || 1}`
        }
      ]
    });

    // Remote info
    if (data.remote) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Pushed to:* ${data.remote}`
        }
      });
    }

    // Commit messages
    if (data.commits && data.commits.length > 0) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: "*Recent Commits:*"
        }
      });
      
      data.commits.slice(0, 5).forEach(commit => {
        blocks.push({
          type: "section",
          text: {
            type: "mrkdwn",
            text: `• \`${commit.hash}\` ${commit.message}`
          }
        });
      });
    }

    // Summary of changes
    if (data.summary) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Summary:* ${data.summary}`
        }
      });
    }

    // Stats
    if (data.stats) {
      blocks.push({
        type: "section",
        fields: [
          {
            type: "mrkdwn",
            text: `*Files Changed:* ${data.stats.filesChanged || 0}`
          },
          {
            type: "mrkdwn",
            text: `*Lines:* +${data.stats.linesAdded || 0} / -${data.stats.linesDeleted || 0}`
          }
        ]
      });
    }

    // Timestamp
    blocks.push({
      type: "context",
      elements: [
        {
          type: "mrkdwn",
          text: `Pushed at: ${new Date().toLocaleString()}`
        }
      ]
    });

    return blocks;
  }
}

module.exports = SlackIntegration; 