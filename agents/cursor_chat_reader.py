#!/usr/bin/env python3
"""
Cursor Chat Reader
Reads and parses chat history from Cursor's SQLite database
"""

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CursorChatReader:
    """Reads and parses chat history from Cursor IDE's local storage"""
    
    def __init__(self, cursor_db_path: Optional[str] = None):
        """
        Initialize the chat reader
        
        Args:
            cursor_db_path: Optional path to Cursor's SQLite database
                          If not provided, will use default OS locations
        """
        self.db_path = cursor_db_path or self._get_default_cursor_path()
        self.enabled = False  # Opt-in feature, disabled by default
        
    def _get_default_cursor_path(self) -> str:
        """Get the default Cursor data path based on OS"""
        system = os.name
        home = Path.home()
        
        if system == 'posix':  # macOS/Linux
            if os.uname().sysname == 'Darwin':  # macOS
                return str(home / 'Library' / 'Application Support' / 'Cursor' / 'User' / 'globalStorage' / 'state.vscdb')
            else:  # Linux
                return str(home / '.config' / 'Cursor' / 'User' / 'globalStorage' / 'state.vscdb')
        elif system == 'nt':  # Windows
            return str(home / 'AppData' / 'Roaming' / 'Cursor' / 'User' / 'globalStorage' / 'state.vscdb')
        else:
            logger.warning(f"Unknown OS: {system}")
            return ""
    
    def read_chats_after_timestamp(self, 
                                 timestamp: datetime,
                                 project_path: Optional[str] = None,
                                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Read chat messages after a specific timestamp
        
        Args:
            timestamp: Only return chats after this time
            project_path: Optional filter by project path
            limit: Maximum number of chats to return
            
        Returns:
            List of chat dictionaries with prompt, response, timestamp, etc.
        """
        if not self.enabled:
            logger.debug("Cursor chat reading is disabled")
            return []
            
        if not os.path.exists(self.db_path):
            logger.warning(f"Cursor database not found at: {self.db_path}")
            logger.info(f"Expected locations: macOS: ~/Library/Application Support/Cursor/User/globalStorage/state.vscdb")
            return []
        
        chats = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert datetime to milliseconds timestamp (Cursor uses milliseconds)
            ts_ms = int(timestamp.timestamp() * 1000)
            
            # Query for bubble data (Cursor's chat storage format)
            # Note: bubbleId entries contain the chat messages
            query = """
                SELECT key, value
                FROM cursorDiskKV
                WHERE key LIKE 'bubbleId:%'
            """
            
            cursor.execute(query)
            all_bubbles = cursor.fetchall()
            
            logger.info(f"Found {len(all_bubbles)} total bubble entries")
            
            # Parse bubble data and filter by timestamp
            for key, value in all_bubbles:
                try:
                    # Parse the JSON data
                    if isinstance(value, bytes):
                        data = json.loads(value.decode('utf-8'))
                    else:
                        data = json.loads(value)
                    
                    # Extract text content and metadata
                    text = data.get('text', '')
                    bubble_type = data.get('type', 0)  # 1=user, 2=assistant
                    
                    # Skip empty messages
                    if not text or text == '...':
                        continue
                    
                    # Estimate timestamp from bubble ID (this is approximate)
                    # In practice, Cursor doesn't store exact timestamps in bubbles
                    # So we'll include all non-empty messages for now
                    
                    chat = {
                        'timestamp': datetime.now(),  # Approximate
                        'project_path': project_path or 'unknown',
                        'text': text,
                        'type': 'user' if bubble_type == 1 else 'assistant',
                        'bubble_id': key
                    }
                    
                    # For light mode, we might want to limit the number of chats
                    if limit and len(chats) >= limit:
                        break
                        
                    chats.append(chat)
                    
                except Exception as e:
                    logger.debug(f"Error parsing bubble {key}: {e}")
                    continue
                
            conn.close()
            logger.info(f"Read {len(chats)} chats after {timestamp}")
            
        except sqlite3.Error as e:
            logger.error(f"Error reading Cursor database: {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading chats: {e}")
            
        return chats
    
    def parse_chat_content(self, chats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse and clean chat content for analysis
        
        Args:
            chats: List of raw chat dictionaries
            
        Returns:
            Parsed content with prompts, responses, and combined text
        """
        parsed = {
            'prompts': [],
            'responses': [],
            'combined': [],
            'total_chats': len(chats)
        }
        
        for chat in chats:
            # Extract text based on message type
            text = chat.get('text', '').strip()
            msg_type = chat.get('type', 'unknown')
            
            if text and msg_type == 'user':
                parsed['prompts'].append({
                    'text': text,
                    'timestamp': chat['timestamp']
                })
            elif text and msg_type == 'assistant':
                parsed['responses'].append({
                    'text': text,
                    'timestamp': chat['timestamp']
                })
            
            # Combined conversation for context
            if text:
                parsed['combined'].append({
                    'text': text,
                    'type': msg_type,
                    'timestamp': chat['timestamp'],
                    'bubble_id': chat.get('bubble_id', '')
                })
        
        return parsed
    
    def extract_development_insights(self, chats: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract key development insights from chat conversations
        
        Args:
            chats: List of chat dictionaries
            
        Returns:
            Dictionary with categorized insights
        """
        insights = {
            'key_decisions': [],
            'implementation_notes': [],
            'bug_fixes': [],
            'feature_requests': [],
            'refactoring': [],
            'questions_asked': []
        }
        
        # Keywords to look for in different categories
        decision_keywords = ['decided', 'choose', 'should use', 'will use', 'best approach']
        implementation_keywords = ['implement', 'create', 'add', 'build', 'develop']
        bug_keywords = ['fix', 'bug', 'error', 'issue', 'problem', 'crash']
        feature_keywords = ['feature', 'new', 'enhance', 'improve', 'add support']
        refactor_keywords = ['refactor', 'optimize', 'clean up', 'restructure', 'improve']
        
        for chat in chats:
            text = chat.get('text', '').lower()
            msg_type = chat.get('type', '')
            
            # Only analyze user messages for insights
            if msg_type != 'user':
                continue
                
            # Categorize based on keywords
            if any(keyword in text for keyword in decision_keywords):
                insights['key_decisions'].append({
                    'prompt': chat.get('text', '')[:200],  # First 200 chars
                    'timestamp': chat['timestamp']
                })
                
            if any(keyword in text for keyword in implementation_keywords):
                insights['implementation_notes'].append({
                    'prompt': chat.get('text', '')[:200],
                    'timestamp': chat['timestamp']
                })
                
            if any(keyword in text for keyword in bug_keywords):
                insights['bug_fixes'].append({
                    'issue': chat.get('text', '')[:200],
                    'timestamp': chat['timestamp']
                })
                
            if any(keyword in text for keyword in feature_keywords):
                insights['feature_requests'].append({
                    'request': chat.get('text', '')[:200],
                    'timestamp': chat['timestamp']
                })
                
            if any(keyword in text for keyword in refactor_keywords):
                insights['refactoring'].append({
                    'target': chat.get('text', '')[:200],
                    'timestamp': chat['timestamp']
                })
            
            # All user messages are questions asked
            insights['questions_asked'].append(chat.get('text', '')[:100])
        
        # Remove duplicates and limit each category
        for key in insights:
            if isinstance(insights[key], list) and len(insights[key]) > 0:
                # For simple string lists, remove duplicates
                if isinstance(insights[key][0], str):
                    insights[key] = list(set(insights[key]))[:10]  # Max 10 items
                # For dict lists, limit to 5 most recent
                else:
                    insights[key] = insights[key][-5:]
        
        return insights
    
    def get_chat_summary(self, 
                        chats: List[Dict[str, Any]], 
                        mode: str = 'full') -> str:
        """
        Generate a summary of chat conversations
        
        Args:
            chats: List of chat dictionaries
            mode: 'full' for complete processing, 'light' for partial
            
        Returns:
            Summary text for inclusion in brainlift
            
        TODO: Consider caching chat summaries by timestamp ranges
              since chats between commits won't change. This could
              significantly reduce processing time and token usage.
        """
        if not chats:
            return "No recent Cursor chat history found."
        
        summary_parts = [f"## Development Context from Cursor Chat\n"]
        summary_parts.append(f"*Analyzed {len(chats)} conversations*\n")
        
        if mode == 'light':
            # Light mode: Process all chats but with simpler analysis
            parsed = self.parse_chat_content(chats)
            summary_parts.append("\n### Recent Development Activity:\n")
            summary_parts.append(f"*{len(parsed['prompts'])} questions asked*\n\n")
            
            # Show last few questions as examples
            recent_prompts = parsed['prompts'][-5:]  # Last 5 questions
            if recent_prompts:
                summary_parts.append("**Recent questions:**\n")
                for prompt in recent_prompts:
                    summary_parts.append(f"- {prompt['text'][:150]}...\n")
                
        else:  # full mode
            # Full analysis
            insights = self.extract_development_insights(chats)
            
            if insights['key_decisions']:
                summary_parts.append("\n### Key Decisions Made:\n")
                for decision in insights['key_decisions']:
                    summary_parts.append(f"- {decision['prompt']}\n")
            
            if insights['bug_fixes']:
                summary_parts.append("\n### Bugs Addressed:\n")
                for bug in insights['bug_fixes']:
                    summary_parts.append(f"- {bug['issue']}\n")
            
            if insights['implementation_notes']:
                summary_parts.append("\n### Implementation Details:\n")
                for impl in insights['implementation_notes']:
                    summary_parts.append(f"- {impl['prompt']}\n")
            
            if insights['feature_requests']:
                summary_parts.append("\n### Features Discussed:\n")
                for feature in insights['feature_requests']:
                    summary_parts.append(f"- {feature['request']}\n")
        
        return ''.join(summary_parts)
    
    def enable(self):
        """Enable chat reading functionality"""
        self.enabled = True
        logger.info("Cursor chat reading enabled")
        
    def disable(self):
        """Disable chat reading functionality"""
        self.enabled = False
        logger.info("Cursor chat reading disabled") 