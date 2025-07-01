#!/usr/bin/env python3
"""
Retry manager for Auto-Brainlift
Handles failed summary generations with exponential backoff
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RetryManager:
    """Manages retries for failed summary generations"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.retry_file = self.base_dir / ".retry_queue.json"
        self.max_retries = int(os.getenv('OPENAI_MAX_RETRIES', '3'))
        self.base_delay = 5  # seconds
        self.max_delay = 300  # 5 minutes
        
    def load_queue(self) -> List[Dict]:
        """Load the retry queue from disk"""
        if not self.retry_file.exists():
            return []
        
        try:
            with open(self.retry_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load retry queue: {e}")
            return []
    
    def save_queue(self, queue: List[Dict]):
        """Save the retry queue to disk"""
        try:
            with open(self.retry_file, 'w') as f:
                json.dump(queue, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save retry queue: {e}")
    
    def add_to_queue(self, commit_hash: str, error: str):
        """Add a failed commit to the retry queue"""
        queue = self.load_queue()
        
        # Check if already in queue
        for item in queue:
            if item['commit_hash'] == commit_hash:
                item['attempts'] += 1
                item['last_error'] = error
                item['last_attempt'] = datetime.now().isoformat()
                self.save_queue(queue)
                return
        
        # Add new entry
        queue.append({
            'commit_hash': commit_hash,
            'attempts': 1,
            'first_attempt': datetime.now().isoformat(),
            'last_attempt': datetime.now().isoformat(),
            'last_error': error
        })
        
        self.save_queue(queue)
        logger.info(f"Added commit {commit_hash[:8]} to retry queue")
    
    def get_next_retry_time(self, attempts: int) -> datetime:
        """Calculate when the next retry should happen using exponential backoff"""
        delay = min(self.base_delay * (2 ** (attempts - 1)), self.max_delay)
        return datetime.now() + timedelta(seconds=delay)
    
    def get_pending_retries(self) -> List[Dict]:
        """Get commits that are ready to retry"""
        queue = self.load_queue()
        pending = []
        
        now = datetime.now()
        for item in queue:
            if item['attempts'] >= self.max_retries:
                continue  # Max retries exceeded
            
            # Calculate when this item can be retried
            last_attempt = datetime.fromisoformat(item['last_attempt'])
            next_retry = self.get_next_retry_time(item['attempts'])
            
            if now >= next_retry:
                pending.append(item)
        
        return pending
    
    def remove_from_queue(self, commit_hash: str):
        """Remove a successfully processed commit from the queue"""
        queue = self.load_queue()
        queue = [item for item in queue if item['commit_hash'] != commit_hash]
        self.save_queue(queue)
        logger.info(f"Removed commit {commit_hash[:8]} from retry queue")
    
    def cleanup_old_entries(self, days: int = 7):
        """Remove entries older than specified days"""
        queue = self.load_queue()
        cutoff = datetime.now() - timedelta(days=days)
        
        new_queue = []
        for item in queue:
            first_attempt = datetime.fromisoformat(item['first_attempt'])
            if first_attempt > cutoff:
                new_queue.append(item)
        
        if len(new_queue) < len(queue):
            self.save_queue(new_queue)
            logger.info(f"Cleaned up {len(queue) - len(new_queue)} old entries from retry queue")


def process_retry_queue():
    """Process any pending retries"""
    import os
    import sys
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from agents.langgraph_agent import GitCommitSummarizer
    from agents.git_hook_handler import mark_commit_processed
    
    retry_manager = RetryManager()
    pending = retry_manager.get_pending_retries()
    
    if not pending:
        logger.info("No pending retries")
        return
    
    logger.info(f"Processing {len(pending)} pending retries")
    
    try:
        summarizer = GitCommitSummarizer()
        
        for item in pending:
            commit_hash = item['commit_hash']
            logger.info(f"Retrying commit {commit_hash[:8]} (attempt {item['attempts'] + 1})")
            
            try:
                result = summarizer.process_commit(commit_hash)
                logger.info(f"Successfully processed commit {commit_hash[:8]} on retry")
                retry_manager.remove_from_queue(commit_hash)
                mark_commit_processed(commit_hash)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Retry failed for commit {commit_hash[:8]}: {error_msg}")
                retry_manager.add_to_queue(commit_hash, error_msg)
                
                # Send notification if max retries exceeded
                if item['attempts'] + 1 >= retry_manager.max_retries:
                    logger.error(f"Max retries exceeded for commit {commit_hash[:8]}")
                    # TODO: Send notification to user
    
    except Exception as e:
        logger.error(f"Error processing retry queue: {e}")
    
    # Cleanup old entries
    retry_manager.cleanup_old_entries()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "retry_manager.log"),
            logging.StreamHandler()
        ]
    )
    
    process_retry_queue() 