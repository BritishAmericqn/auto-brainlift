#!/usr/bin/env python3
"""
Git hook handler for Auto-Brainlift
Called by post-commit hook to generate summaries
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import git

# Load environment variables
load_dotenv()

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "git_hook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_latest_commit_hash():
    """Get the hash of the latest commit"""
    try:
        repo = git.Repo(Path(__file__).parent.parent)
        return str(repo.head.commit.hexsha)
    except Exception as e:
        logger.error(f"Failed to get latest commit: {e}")
        return None


def is_commit_processed(commit_hash):
    """Check if a commit has already been processed"""
    processed_file = Path(__file__).parent.parent / ".processed_commits"
    
    if not processed_file.exists():
        return False
    
    try:
        with open(processed_file, 'r') as f:
            for line in f:
                if line.strip() and commit_hash in line:
                    return True
        return False
    except Exception as e:
        logger.error(f"Error reading processed commits: {e}")
        return False


def mark_commit_processed(commit_hash):
    """Mark a commit as processed"""
    processed_file = Path(__file__).parent.parent / ".processed_commits"
    
    try:
        with open(processed_file, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{commit_hash} {timestamp}\n")
        logger.info(f"Marked commit {commit_hash[:8]} as processed")
    except Exception as e:
        logger.error(f"Failed to mark commit as processed: {e}")


def should_skip_commit(repo, commit_hash):
    """Check if we should skip this commit based on commit message"""
    try:
        commit = repo.commit(commit_hash)
        message = commit.message.lower().strip()
        
        # Skip commits with certain keywords
        skip_keywords = [
            '[skip-brainlift]',
            '[skip brainlift]',
            'wip:',
            'merge branch',
            'merge pull request'
        ]
        
        for keyword in skip_keywords:
            if keyword in message:
                logger.info(f"Skipping commit {commit_hash[:8]} due to keyword: {keyword}")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking commit message: {e}")
        return False


def trigger_summary_generation(commit_hash):
    """Trigger the LangGraph agent to generate summaries"""
    try:
        # Check if Git hook is enabled
        if os.getenv('GIT_HOOK_ENABLED', 'true').lower() != 'true':
            logger.info("Git hook is disabled via GIT_HOOK_ENABLED env var")
            return
        
        # Get the Python executable (prefer venv)
        venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else "python3"
        
        # Path to the LangGraph agent
        agent_path = Path(__file__).parent / "langgraph_agent.py"
        
        logger.info(f"Triggering summary generation for commit {commit_hash[:8]}")
        
        # Run the agent
        result = subprocess.run(
            [python_cmd, str(agent_path), commit_hash],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Summary generation completed successfully")
            mark_commit_processed(commit_hash)
            
            # Check if this was in the retry queue, remove it
            try:
                from agents.retry_manager import RetryManager
                retry_manager = RetryManager()
                retry_manager.remove_from_queue(commit_hash)
            except:
                pass  # Retry manager is optional
            
            # Send notification to Electron app if running
            try:
                notification_script = Path(__file__).parent.parent / "ui" / "notify.js"
                if notification_script.exists():
                    subprocess.run(["node", str(notification_script), "complete"], capture_output=True)
            except:
                pass  # Notification is optional
        else:
            logger.error(f"Summary generation failed: {result.stderr}")
            # Add to retry queue
            try:
                from agents.retry_manager import RetryManager
                retry_manager = RetryManager()
                retry_manager.add_to_queue(commit_hash, result.stderr or "Unknown error")
                logger.info(f"Added commit {commit_hash[:8]} to retry queue")
            except Exception as e:
                logger.error(f"Failed to add to retry queue: {e}")
            
    except Exception as e:
        logger.error(f"Failed to trigger summary generation: {e}")


def main():
    """Main entry point for Git hook"""
    try:
        # Get the latest commit
        commit_hash = get_latest_commit_hash()
        if not commit_hash:
            logger.error("Could not get latest commit hash")
            return
        
        logger.info(f"Post-commit hook triggered for {commit_hash[:8]}")
        
        # Check if already processed
        if is_commit_processed(commit_hash):
            logger.info(f"Commit {commit_hash[:8]} already processed, skipping")
            return
        
        # Check if we should skip this commit
        repo = git.Repo(Path(__file__).parent.parent)
        if should_skip_commit(repo, commit_hash):
            mark_commit_processed(commit_hash)  # Mark as processed so we don't check again
            return
        
        # Trigger summary generation
        trigger_summary_generation(commit_hash)
        
    except Exception as e:
        logger.error(f"Git hook error: {e}")
        # Don't fail the commit
        sys.exit(0)


if __name__ == "__main__":
    main() 