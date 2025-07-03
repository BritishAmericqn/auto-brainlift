#!/usr/bin/env python3
"""
Cursor Chat Agent
Analyzes development context from Cursor chat conversations
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from agents.base_agent import AgentState, SpecializedAgent
from agents.cursor_chat_reader import CursorChatReader

logger = logging.getLogger(__name__)

CURSOR_CHAT_PROMPT = """You are an AI assistant specializing in analyzing developer chat conversations.
Your task is to extract key insights, decisions, and context from Cursor IDE chat history.

Given the following chat conversations between a developer and AI assistant:

{chat_content}

Please analyze these conversations and provide:

1. **Development Context Score** (0-100): How much useful context do these chats provide?
2. **Key Decisions**: Important technical decisions made during the conversations
3. **Problem Solving**: Issues discussed and their resolutions
4. **Implementation Details**: Specific implementation guidance provided
5. **Learning Points**: What the developer learned or clarified
6. **Unresolved Questions**: Any questions or issues left unanswered

Format your response as a JSON object with the following structure:
```json
{
  "context_score": <int>,
  "key_decisions": [<list of decisions>],
  "problems_solved": [{"problem": <str>, "solution": <str>}],
  "implementation_guidance": [<list of implementation details>],
  "learning_points": [<list of learnings>],
  "unresolved_questions": [<list of questions>],
  "summary": "<brief narrative summary>"
}
```

Focus on extracting actionable insights that help understand the development process."""


class CursorChatAgent(SpecializedAgent):
    """Agent specialized in analyzing Cursor chat conversations"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="cursor_chat",
            prompt_template=CURSOR_CHAT_PROMPT,
            cost_per_1k_tokens=0.01,  # Default to GPT-4 turbo pricing
            **kwargs
        )
        self.chat_reader = None
        self._init_chat_reader()
        
    def _init_chat_reader(self):
        """Initialize the Cursor chat reader"""
        try:
            # Get configuration
            chat_path = os.getenv('CURSOR_CHAT_PATH')  # Optional custom path
            self.chat_reader = CursorChatReader(chat_path)
            
            # Enable the reader if this agent is enabled
            if self.enabled:
                self.chat_reader.enable()
                logger.info("Cursor chat reader initialized and enabled")
            else:
                logger.info("Cursor chat reader initialized but disabled")
                
        except Exception as e:
            logger.error(f"Failed to initialize Cursor chat reader: {e}")
            self.chat_reader = None
    
    def analyze(self, state: AgentState) -> AgentState:
        """Analyze Cursor chat conversations"""
        if not self.enabled or not self.chat_reader:
            logger.info("Cursor chat agent disabled or not initialized")
            return state
            
        try:
            # Get chat processing mode
            chat_mode = os.getenv('CURSOR_CHAT_MODE', 'light')
            
            # Determine time range for chat analysis
            commit_info = state.get("commit_info", {})
            if state.get("wip_mode"):
                # For WIP analysis, look at recent chats
                start_time = datetime.now() - timedelta(hours=4)
            else:
                # For commit analysis, try to get previous commit time
                # This is simplified - in practice would need git integration
                start_time = datetime.now() - timedelta(hours=24)
            
            # Read chats
            project_path = os.getenv("PROJECT_PATH", str(Path.cwd()))
            
            if chat_mode == 'light':
                chats = self.chat_reader.read_chats_after_timestamp(
                    start_time,
                    project_path=project_path
                )
            else:
                # Full mode: more historical context
                extended_start_time = datetime.now() - timedelta(days=7)
                chats = self.chat_reader.read_chats_after_timestamp(
                    extended_start_time,
                    project_path=project_path,
                    limit=50
                )
            
            logger.info(f"Found {len(chats)} chats to analyze")
            
            if not chats:
                # No chats found
                return self.update_state(state, {
                    "analysis": {
                        "context_score": 0,
                        "key_decisions": [],
                        "problems_solved": [],
                        "implementation_guidance": [],
                        "learning_points": [],
                        "unresolved_questions": [],
                        "summary": "No Cursor chat conversations found for this time period."
                    },
                    "chat_count": 0,
                    "tokens_used": 0,
                    "cost": 0
                })
            
            # Parse chats for content
            parsed_chats = self.chat_reader.parse_chat_content(chats)
            
            # Create a structured chat content for analysis
            chat_content = self._format_chats_for_analysis(parsed_chats)
            
            # Use LLM to analyze if we have substantial content
            if len(chat_content) > 200:  # Minimal threshold
                # Format prompt
                prompt = self.prompt_template.format(chat_content=chat_content)
                
                # Call parent's analyze for LLM processing
                state["cursor_chat_content"] = chat_content
                state = super().analyze(state)
                
                # Add chat metadata
                if f"agent_{self.name}" in state:
                    state[f"agent_{self.name}"]["chat_count"] = len(chats)
                    state[f"agent_{self.name}"]["chat_mode"] = chat_mode
                    state[f"agent_{self.name}"]["time_range"] = f"Last {(datetime.now() - start_time).days} days"
            else:
                # Too little content for LLM analysis
                # Use basic extraction from chat reader
                insights = self.chat_reader.extract_development_insights(chats)
                
                return self.update_state(state, {
                    "analysis": {
                        "context_score": 25,  # Low score for minimal content
                        "key_decisions": insights.get("key_decisions", []),
                        "problems_solved": [],
                        "implementation_guidance": insights.get("implementation_notes", []),
                        "learning_points": [],
                        "unresolved_questions": [],
                        "summary": f"Found {len(chats)} brief chat exchanges with limited context."
                    },
                    "chat_count": len(chats),
                    "tokens_used": 0,
                    "cost": 0
                })
                
        except Exception as e:
            logger.error(f"Error in Cursor chat analysis: {e}")
            return self.update_state(state, {
                "error": str(e),
                "analysis": {
                    "context_score": 0,
                    "summary": f"Error analyzing chats: {str(e)}"
                }
            })
            
        return state
    
    def _format_chats_for_analysis(self, parsed_chats: Dict[str, Any]) -> str:
        """Format parsed chats into a string for LLM analysis"""
        formatted = []
        
        # Combine prompts and responses in chronological order
        combined = parsed_chats.get("combined", [])
        
        for i, chat in enumerate(combined[:30]):  # Limit to prevent token overflow
            msg_type = chat.get("type", "unknown")
            text = chat.get("text", "").strip()
            
            if text:
                if msg_type == "user":
                    formatted.append(f"DEVELOPER: {text}")
                elif msg_type == "assistant":
                    formatted.append(f"AI ASSISTANT: {text}")
                formatted.append("")  # Empty line between exchanges
        
        return "\n".join(formatted)
    
    def get_prompt(self) -> str:
        """Get the specialized prompt for cursor chat analysis"""
        return CURSOR_CHAT_PROMPT 