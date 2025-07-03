"""
Push notification handler for Auto-Brainlift
Called by pre-push hook to send notifications to Slack
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
log_dir = Path.home() / "Library" / "Application Support" / "auto-brainlift" / "logs"
log_dir.mkdir(exist_ok=True, parents=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "push_notifications.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_global_settings():
    """Read global settings to get Slack configuration"""
    try:
        settings_path = Path.home() / "Library" / "Application Support" / "auto-brainlift" / "global-settings.json"
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error reading global settings: {e}")
    return {}


def get_project_info():
    """Get current project information"""
    try:
        # Read projects.json to find the project for current directory
        projects_path = Path.home() / "Library" / "Application Support" / "auto-brainlift" / "projects.json"
        current_path = os.getcwd()
        
        if projects_path.exists():
            with open(projects_path, 'r') as f:
                projects_data = json.load(f)
                
                # Find project by path
                for project_id, project_info in projects_data.get('projects', {}).items():
                    if project_info.get('path') == current_path:
                        return project_info
                        
    except Exception as e:
        logger.error(f"Error reading project info: {e}")
    
    # Default project info
    return {
        'name': Path(current_path).name,
        'id': 'unknown'
    }


def get_commit_info(sha):
    """Get commit information"""
    try:
        result = subprocess.run(
            ['git', 'log', '--format=%H %s', '-1', sha],
            capture_output=True,
            text=True,
            check=True
        )
        parts = result.stdout.strip().split(' ', 1)
        return {
            'hash': parts[0][:8],
            'message': parts[1] if len(parts) > 1 else 'No message'
        }
    except Exception as e:
        logger.error(f"Error getting commit info: {e}")
        return {
            'hash': sha[:8],
            'message': 'Unable to get commit message'
        }


def get_push_summary():
    """Generate a summary of the push"""
    branch = os.getenv('PUSH_BRANCH', 'unknown')
    commit_count = os.getenv('PUSH_COMMITS', '0')
    remote = os.getenv('PUSH_REMOTE', 'origin')
    local_sha = os.getenv('PUSH_LOCAL_SHA', '')
    remote_sha = os.getenv('PUSH_REMOTE_SHA', '')
    
    # Get list of commits being pushed
    commits = []
    try:
        if remote_sha == '0000000000000000000000000000000000000000':
            # New branch - get last 5 commits
            cmd = ['git', 'log', '--format=%H', '-5', local_sha]
        else:
            # Existing branch - get commits in range
            cmd = ['git', 'log', '--format=%H', f'{remote_sha}..{local_sha}']
            
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        for sha in result.stdout.strip().split('\n'):
            if sha:
                commits.append(get_commit_info(sha))
                
    except Exception as e:
        logger.error(f"Error getting commits: {e}")
    
    # Get diff stats
    stats = {'filesChanged': 0, 'linesAdded': 0, 'linesDeleted': 0}
    try:
        if remote_sha != '0000000000000000000000000000000000000000':
            result = subprocess.run(
                ['git', 'diff', '--shortstat', f'{remote_sha}..{local_sha}'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse: "X files changed, Y insertions(+), Z deletions(-)"
            import re
            match = re.search(r'(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?', result.stdout)
            if match:
                stats['filesChanged'] = int(match.group(1) or 0)
                stats['linesAdded'] = int(match.group(2) or 0)
                stats['linesDeleted'] = int(match.group(3) or 0)
    except Exception as e:
        logger.error(f"Error getting diff stats: {e}")
    
    # Generate summary text
    summary_parts = []
    if int(commit_count) == 1:
        summary_parts.append(f"Pushing 1 commit to {branch}")
    else:
        summary_parts.append(f"Pushing {commit_count} commits to {branch}")
        
    if stats['filesChanged'] > 0:
        summary_parts.append(f"{stats['filesChanged']} files changed (+{stats['linesAdded']}/-{stats['linesDeleted']})")
    
    return {
        'branch': branch,
        'commitCount': int(commit_count),
        'remote': remote,
        'commits': commits[:5],  # Limit to 5 most recent
        'stats': stats,
        'summary': ' - '.join(summary_parts)
    }


def send_slack_notification(push_data, project_info, settings):
    """Send push notification to Slack"""
    try:
        # We can't import SlackIntegration from Python since it's a Node.js module
        # Instead, we'll use the Slack Web API directly
        slack_token = settings['slackToken']
        channel = settings.get('slackChannel', '#dev-updates')
        
        # Build the message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚀 Code Push: {project_info['name']}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Branch:* {push_data['branch']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Commits:* {push_data['commitCount']}"
                    }
                ]
            }
        ]
        
        # Add remote info if available
        if push_data.get('remote'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Pushed to:* {push_data['remote']}"
                }
            })
        
        # Add recent commits
        if push_data.get('commits'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Recent Commits:*"
                }
            })
            
            for commit in push_data['commits'][:5]:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• `{commit['hash']}` {commit['message']}"
                    }
                })
        
        # Add stats
        if push_data.get('stats'):
            stats = push_data['stats']
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Files Changed:* {stats.get('filesChanged', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Lines:* +{stats.get('linesAdded', 0)} / -{stats.get('linesDeleted', 0)}"
                    }
                ]
            })
        
        # Add timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Pushed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        # Send to Slack using web API
        headers = {
            'Authorization': f'Bearer {slack_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'channel': channel,
            'text': f"🚀 Code Push: {project_info['name']}",
            'blocks': blocks
        }
        
        response = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info("Slack notification sent successfully")
                return {'success': True}
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"Slack API error: {error}")
                return {'success': False, 'error': error}
        else:
            logger.error(f"HTTP error {response.status_code}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        return {'success': False, 'error': str(e)}


def main():
    """Main entry point for push notification handler"""
    try:
        # Check if Git hook is enabled
        if os.getenv('GIT_HOOK_ENABLED', 'true').lower() != 'true':
            logger.info("Git hook is disabled via GIT_HOOK_ENABLED env var")
            return
        
        # Get settings
        settings = get_global_settings()
        
        # Check if Slack is enabled
        if not settings.get('slackEnabled'):
            logger.info("Slack notifications are disabled")
            return
            
        if not settings.get('slackToken'):
            logger.error("Slack token not configured")
            return
        
        # Get project info
        project_info = get_project_info()
        logger.info(f"Processing push for project: {project_info['name']}")
        
        # Get push summary
        push_data = get_push_summary()
        logger.info(f"Push summary: {push_data['summary']}")
        
        # Send to Slack
        result = send_slack_notification(push_data, project_info, settings)
        
        if result['success']:
            logger.info("Push notification completed successfully")
        else:
            logger.error(f"Push notification failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Push notification handler error: {e}")
        # Don't exit with error to avoid blocking the push
        
    sys.exit(0)


if __name__ == "__main__":
    main() 