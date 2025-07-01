#!/usr/bin/env python3
"""
Base Agent Framework for Multi-Agent System
Provides common functionality for all specialized agents
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


class AgentState(dict):
    """Shared state for agent communication"""
    pass


class BaseAgent(ABC):
    """Abstract base class for all specialized agents"""
    
    def __init__(self, name: str, model: str = "gpt-4-turbo", 
                 tools: Optional[List[Callable]] = None,
                 cost_per_1k_tokens: float = 0.01,
                 enabled: bool = True):
        self.name = name
        self.model = model
        self.tools = tools or []
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.enabled = enabled
        self.llm = ChatOpenAI(model=model)
        
        # Agent-specific state
        self.state = {}
        
    @abstractmethod
    def analyze(self, state: AgentState) -> AgentState:
        """Main analysis method - must be implemented by subclasses"""
        pass
    
    def estimate_cost(self, text: str) -> float:
        """Estimate cost for processing text"""
        # Rough estimate: 4 chars per token
        tokens = len(text) / 4
        return (tokens / 1000) * self.cost_per_1k_tokens
    
    def update_state(self, state: AgentState, updates: Dict[str, Any]) -> AgentState:
        """Update shared state with agent results"""
        agent_key = f"agent_{self.name}"
        if agent_key not in state:
            state[agent_key] = {}
        state[agent_key].update(updates)
        state[agent_key]["timestamp"] = datetime.now().isoformat()
        return state
    
    def get_prompt(self) -> str:
        """Get agent-specific prompt - can be overridden"""
        return f"You are a {self.name} agent analyzing code changes."
    
    def __str__(self):
        return f"{self.name} Agent (Model: {self.model}, Enabled: {self.enabled})"


class SpecializedAgent(BaseAgent):
    """Base class for specialized agents with common patterns"""
    
    def __init__(self, name: str, prompt_template: str, **kwargs):
        super().__init__(name, **kwargs)
        self.prompt_template = prompt_template
        
    def analyze(self, state: AgentState) -> AgentState:
        """Common analysis pattern for specialized agents"""
        try:
            # Get input from state
            git_diff = state.get("git_diff", "")
            commit_info = state.get("commit_info", {})
            
            # Check if we should run
            if not self.enabled or not git_diff:
                return self.update_state(state, {"skipped": True, "reason": "No input or disabled"})
            
            # Build prompt
            prompt = self.prompt_template.format(
                commit_hash=commit_info.get("commit_hash", ""),
                commit_message=commit_info.get("commit_message", ""),
                git_diff=git_diff[:3000]  # Limit diff size
            )
            
            # Get LLM response
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Process response
            analysis_result = self.process_response(response.content)
            
            # Update state with results
            return self.update_state(state, {
                "analysis": analysis_result,
                "tokens_used": len(prompt) // 4 + len(response.content) // 4,
                "cost": self.estimate_cost(prompt + response.content)
            })
            
        except Exception as e:
            logger.error(f"Error in {self.name} analysis: {e}")
            return self.update_state(state, {"error": str(e)})
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process LLM response - can be overridden by subclasses"""
        return {"raw_response": response} 