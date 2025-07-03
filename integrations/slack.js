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
        blocks: blocks,
        text: `New brainlift for ${projectName}: ${data.overallScore}/100`
      });
      
      return { 
        success: true, 
        ts: result.ts, 
        channel: result.channel 
      };
    } catch (error) {
      console.error('Slack send error:', error);
      return { 
        success: false, 
        error: error.message 
      };
    }
  }

  formatBrainliftMessage(data, projectName) {
    const { overallScore, securityScore, qualityScore, commitInfo, criticalIssues } = data;
    
    const blocks = [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: `🧠 Brainlift Summary: ${projectName}`,
          emoji: true
        }
      },
      {
        type: "section",
        fields: [
          {
            type: "mrkdwn",
            text: `*Overall Score:* ${this.getScoreEmoji(overallScore)} ${overallScore}/100`
          },
          {
            type: "mrkdwn",
            text: `*Commit:* \`${commitInfo.hash.substring(0, 7)}\``
          },
          {
            type: "mrkdwn",
            text: `*Security:* ${this.getScoreEmoji(securityScore)} ${securityScore}/100`
          },
          {
            type: "mrkdwn",
            text: `*Quality:* ${this.getScoreEmoji(qualityScore)} ${qualityScore}/100`
          }
        ]
      }
    ];

    if (commitInfo.message) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*Commit Message:* ${commitInfo.message}`
        }
      });
    }

    if (criticalIssues && criticalIssues.length > 0) {
      blocks.push({
        type: "divider"
      });
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*⚠️ Critical Issues Found:*\n${criticalIssues.map(issue => `• ${issue}`).join('\n')}`
        }
      });
    }

    blocks.push({
      type: "context",
      elements: [
        {
          type: "mrkdwn",
          text: `Generated at ${new Date().toLocaleString()} | Auto-Brainlift v2.1`
        }
      ]
    });

    return blocks;
  }

  getScoreEmoji(score) {
    if (score >= 90) return '🟢';
    if (score >= 70) return '🟡';
    if (score >= 50) return '🟠';
    return '🔴';
  }
}

module.exports = SlackIntegration; 