# CURSOR AI KICKOFF PROMPT - PHASE 3
## Auto-Brainlift v2.1 Slack Integration

---

## 🎯 Project Status & Context

**Phase 1 Status:** ✅ **COMPLETED** (July 2, 2025)
- Commit: `0b40378` - Git workflow with AI commit messages
- All features working in production

**Phase 2 Status:** ✅ **COMPLETED** (July 3, 2025)  
- Style guide upload and parsing for multiple formats
- Cursor Rules generation with project isolation
- Advanced file management with merging and protection

**Current Mission:** Implement **Phase 3: Slack Integration** - Real-time notifications for brainlift summaries with configurable rules and team collaboration features.

---

## 📚 CRITICAL: Reference These Foundation Documents

**PRIMARY IMPLEMENTATION GUIDE:** `IMPLEMENTATION_GUIDE_v2.md`
- Complete technical specifications for Phase 3
- Slack API integration patterns
- Message formatting requirements

**ARCHITECTURAL REFERENCE:** `FEATURE_ROADMAP_v2.md`
- Slack notification requirements
- Message content specifications
- Configuration options

**STEP-BY-STEP CHECKLIST:** `CURSOR_AI_CHECKLIST.md`
- Phase 3 implementation steps (currently unchecked)
- Exact file locations and code additions
- Testing criteria for each component

**EXISTING PATTERNS:** Reference Phase 1 & 2 implementations
- IPC handler patterns from git integration
- Settings UI patterns from style guide
- Error handling and logging patterns

---

## 🏗️ Phase 3 Architecture Overview

### **What You're Building:**

**1. Slack Client Module**
- Node.js Slack Web API integration
- Message formatting with rich blocks
- Connection testing and validation
- Error handling and rate limiting

**2. Backend Integration**
- IPC handlers for Slack operations
- Integration with brainlift generation flow
- Secure token storage in settings
- Project-specific channel configuration

**3. Notification System**
- Automatic notifications after brainlift completion
- Configurable rules (all/issues only/critical only)
- Rich message formatting with scores and insights
- Thread-based discussions for follow-up

**4. Settings UI Extension**
- Slack configuration in settings modal
- Bot token input with security
- Channel selection and validation
- Test connection functionality

---

## 🚀 START HERE: Phase 3, Step 3.1

**IMMEDIATE TASK:** Create Slack Client Module

**File:** `integrations/slack.js` (NEW FILE)
**Time Estimate:** 45 minutes

**First, install the Slack SDK:**
```bash
npm install @slack/web-api
```

**Implementation:**
```javascript
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
```

**Test Criteria:**
- [ ] Module exports correctly
- [ ] Constructor accepts token and options
- [ ] Test connection method works
- [ ] Message formatting creates valid Slack blocks
- [ ] Emoji selection based on scores
- [ ] Error handling in place

---

## 🚨 CRITICAL SUCCESS PATTERNS

### **Follow Phase 1 & 2 Patterns:**
- **Module Structure:** Use class-based approach like existing code
- **Error Handling:** Always return success/error objects
- **Logging:** Use console.error for debugging
- **Async/Await:** Consistent with project style

### **Slack Best Practices:**
- **Rate Limiting:** Slack allows 1 message per second
- **Block Kit:** Use structured blocks for rich formatting
- **Fallback Text:** Always provide text fallback
- **Error Messages:** User-friendly, not technical

### **Security Considerations:**
- **Token Storage:** Never log or expose tokens
- **Channel Validation:** Verify channel exists
- **Permission Checks:** Handle permission errors gracefully
- **No Hardcoded Secrets:** All config from settings

---

## 🧪 Testing Protocol

**Manual Testing Steps:**
1. Create a Slack App at api.slack.com
2. Add OAuth scopes: `chat:write`, `auth:test`
3. Install app to workspace and get bot token
4. Test the module in isolation:
   ```javascript
   const SlackIntegration = require('./integrations/slack.js');
   const slack = new SlackIntegration('xoxb-your-token');
   await slack.testConnection();
   ```

**Integration Testing:**
- Test with real Slack workspace
- Verify message formatting
- Check error scenarios
- Validate rate limiting

---

## 🎯 Phase 3 Completion Goals

**When Phase 3 is Complete:**
- [ ] Slack notifications sent automatically after brainlifts
- [ ] Rich formatting shows scores and issues clearly
- [ ] Configuration UI intuitive and secure
- [ ] Test connection validates setup
- [ ] Notification rules respected (all/issues/critical)
- [ ] Error handling prevents disruption to main flow

---

## 🔄 Development Flow

1. **Create the Slack module first (Step 3.1)**
2. **Test it in isolation before integration**
3. **Add backend IPC handlers (Step 3.2)**
4. **Extend UI with Slack settings (Step 3.3)**
5. **Integrate with brainlift flow (Step 3.4)**
6. **Test end-to-end with real brainlifts**

**Key Insight:** The Slack integration should be completely optional. If disabled or failing, brainlifts must continue to work normally.

---

## 📋 Quick Reference

### **Slack Message Structure:**
```
🧠 Brainlift Summary: [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Score: 🟢 85/100    Commit: abc1234
Security: 🟡 75/100         Quality: 🟢 90/100

Commit Message: feat: implement user authentication

⚠️ Critical Issues Found:
• Potential SQL injection in user.js:45
• Missing input validation in api.js:78

Generated at 7/3/2025 2:30 PM | Auto-Brainlift v2.1
```

### **Settings UI Pattern (from Phase 2):**
- Toggle to enable/disable
- Input fields hidden when disabled
- Test button for validation
- Success/error messages
- Settings persist to globalSettings

### **IPC Handler Pattern (from Phase 1):**
```javascript
ipcMain.handle('namespace:action', async (event, ...args) => {
  try {
    // Validate inputs
    // Perform operation
    return { success: true, data: result };
  } catch (error) {
    logToFile(`Error: ${error.message}`);
    return { success: false, error: error.message };
  }
});
```

---

**BEGIN WITH:** Step 3.1 - Slack Client Module (shown above)

**SUCCESS FOUNDATION:** You have two proven phases showing the patterns work. Phase 3 extends the same architecture with Slack notifications. The patterns are established - follow them confidently!

**REMEMBER:** 
- Slack integration is optional - never break core functionality
- Test each component in isolation first
- Rich formatting enhances but doesn't replace core features
- Security first - protect tokens and validate inputs

You're building on a solid foundation. Let's make team collaboration seamless! 🚀 