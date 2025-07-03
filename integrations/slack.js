const { WebClient } = require('@slack/web-api');

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
}

module.exports = SlackIntegration; 