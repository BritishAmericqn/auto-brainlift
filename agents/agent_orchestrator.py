#!/usr/bin/env python3
"""
Agent Orchestrator
Manages the multi-agent system and coordinates agent execution
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

from agents.base_agent import AgentState, BaseAgent
from agents.security_agent import SecurityAgent
from agents.quality_agent import QualityAgent
from agents.documentation_agent import DocumentationAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple specialized agents for comprehensive code analysis"""
    
    def __init__(self, project_id: str, settings: Optional[Dict[str, Any]] = None):
        self.project_id = project_id
        self.settings = settings or {}
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Track execution metrics
        self.metrics = {
            "agents_run": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "execution_time": 0.0
        }
        
    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all available agents"""
        agent_configs = self.settings.get("agents", {})
        
        agents = {
            "security": SecurityAgent(
                enabled=agent_configs.get("security", {}).get("enabled", True),
                model=agent_configs.get("security", {}).get("model", "gpt-4-turbo")
            ),
            "quality": QualityAgent(
                enabled=agent_configs.get("quality", {}).get("enabled", True),
                model=agent_configs.get("quality", {}).get("model", "gpt-4-turbo")
            ),
            "documentation": DocumentationAgent(
                enabled=agent_configs.get("documentation", {}).get("enabled", True),
                model=agent_configs.get("documentation", {}).get("model", "gpt-4-turbo")
            )
        }
        
        logger.info(f"Initialized {len(agents)} agents for project {self.project_id}")
        return agents
    
    def analyze_commit(self, git_diff: str, commit_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a commit using all enabled agents"""
        start_time = datetime.now()
        
        # Initialize shared state
        state = AgentState({
            "git_diff": git_diff,
            "commit_info": commit_info,
            "project_id": self.project_id,
            "timestamp": start_time.isoformat()
        })
        
        # Determine execution mode
        execution_mode = self.settings.get("execution_mode", "parallel")
        
        if execution_mode == "parallel":
            state = self._run_agents_parallel(state)
        elif execution_mode == "sequential":
            state = self._run_agents_sequential(state)
        elif execution_mode == "priority":
            state = self._run_agents_priority(state)
        else:
            logger.warning(f"Unknown execution mode: {execution_mode}, defaulting to parallel")
            state = self._run_agents_parallel(state)
        
        # Calculate final metrics
        elapsed_time = (datetime.now() - start_time).total_seconds()
        self.metrics["execution_time"] = elapsed_time
        
        # Aggregate results
        results = self._aggregate_results(state)
        results["metrics"] = self.metrics
        
        logger.info(f"Analysis complete in {elapsed_time:.2f}s")
        return results
    
    def _run_agents_parallel(self, state: AgentState) -> AgentState:
        """Run all enabled agents in parallel"""
        enabled_agents = [(name, agent) for name, agent in self.agents.items() if agent.enabled]
        
        if not enabled_agents:
            logger.warning("No agents enabled")
            return state
        
        # Run agents in parallel using ThreadPoolExecutor
        futures = []
        for name, agent in enabled_agents:
            future = self.executor.submit(agent.analyze, AgentState(state.copy()))
            futures.append((name, future))
        
        # Collect results
        for name, future in futures:
            try:
                agent_state = future.result(timeout=30)  # 30 second timeout per agent
                # Merge agent results into main state
                if f"agent_{name}" in agent_state:
                    state[f"agent_{name}"] = agent_state[f"agent_{name}"]
                    self._update_metrics(agent_state[f"agent_{name}"])
                self.metrics["agents_run"] += 1
            except Exception as e:
                logger.error(f"Error running {name} agent: {e}")
                state[f"agent_{name}"] = {"error": str(e)}
        
        return state
    
    def _run_agents_sequential(self, state: AgentState) -> AgentState:
        """Run agents sequentially, passing state between them"""
        enabled_agents = [(name, agent) for name, agent in self.agents.items() if agent.enabled]
        
        for name, agent in enabled_agents:
            try:
                state = agent.analyze(state)
                if f"agent_{name}" in state:
                    self._update_metrics(state[f"agent_{name}"])
                self.metrics["agents_run"] += 1
            except Exception as e:
                logger.error(f"Error running {name} agent: {e}")
                state[f"agent_{name}"] = {"error": str(e)}
        
        return state
    
    def _run_agents_priority(self, state: AgentState) -> AgentState:
        """Run agents based on priority settings"""
        # Get agent priorities from settings
        priorities = self.settings.get("agent_priorities", {
            "security": 1,
            "quality": 2,
            "documentation": 3
        })
        
        # Sort agents by priority
        sorted_agents = sorted(
            [(name, agent) for name, agent in self.agents.items() if agent.enabled],
            key=lambda x: priorities.get(x[0], 999)
        )
        
        # Run in priority order
        for name, agent in sorted_agents:
            try:
                # Check if we should continue based on previous results
                if self._should_continue(state):
                    state = agent.analyze(state)
                    if f"agent_{name}" in state:
                        self._update_metrics(state[f"agent_{name}"])
                    self.metrics["agents_run"] += 1
            except Exception as e:
                logger.error(f"Error running {name} agent: {e}")
                state[f"agent_{name}"] = {"error": str(e)}
        
        return state
    
    def _should_continue(self, state: AgentState) -> bool:
        """Determine if we should continue running agents based on current state"""
        # Check budget limits
        budget_enabled = self.settings.get("budgetEnabled", False)
        if budget_enabled:
            budget_limit = self.settings.get("commitTokenLimit", 10000)
            if self.metrics["total_tokens"] >= budget_limit:
                logger.warning(f"Token budget exceeded: {self.metrics['total_tokens']} >= {budget_limit}")
                return False
        
        # Check for critical security issues
        if "agent_security" in state:
            security_result = state["agent_security"].get("analysis", {})
            if security_result.get("severity") == "high":
                logger.info("High severity security issue found, may skip other agents")
                # Could implement logic to skip non-critical agents
        
        return True
    
    def _update_metrics(self, agent_result: Dict[str, Any]):
        """Update execution metrics from agent result"""
        if "tokens_used" in agent_result:
            self.metrics["total_tokens"] += agent_result["tokens_used"]
        if "cost" in agent_result:
            self.metrics["total_cost"] += agent_result["cost"]
    
    def _aggregate_results(self, state: AgentState) -> Dict[str, Any]:
        """Aggregate results from all agents into a unified summary"""
        results = {
            "project_id": self.project_id,
            "timestamp": state.get("timestamp"),
            "commit_info": state.get("commit_info"),
            "agents": {}
        }
        
        # Collect individual agent results
        for key, value in state.items():
            if key.startswith("agent_"):
                agent_name = key.replace("agent_", "")
                results["agents"][agent_name] = value
        
        # Generate overall summary
        results["summary"] = self._generate_summary(results["agents"])
        
        # Calculate overall scores
        results["overall_scores"] = {
            "security": results["agents"].get("security", {}).get("analysis", {}).get("security_score", 100),
            "quality": results["agents"].get("quality", {}).get("analysis", {}).get("quality_score", 70),
            "documentation": results["agents"].get("documentation", {}).get("analysis", {}).get("documentation_score", 50)
        }
        
        return results
    
    def _generate_summary(self, agent_results: Dict[str, Any]) -> str:
        """Generate a unified summary from all agent results"""
        summary_parts = []
        
        # Security summary
        if "security" in agent_results and "analysis" in agent_results["security"]:
            security = agent_results["security"]["analysis"]
            if security.get("severity", "none") != "none":
                summary_parts.append(f"Security: {security.get('severity')} severity issues found")
        
        # Quality summary
        if "quality" in agent_results and "analysis" in agent_results["quality"]:
            quality = agent_results["quality"]["analysis"]
            score = quality.get("quality_score", 0)
            summary_parts.append(f"Code Quality: {score}/100")
        
        # Documentation summary
        if "documentation" in agent_results and "analysis" in agent_results["documentation"]:
            docs = agent_results["documentation"]["analysis"]
            score = docs.get("documentation_score", 0)
            summary_parts.append(f"Documentation: {score}/100")
        
        return " | ".join(summary_parts) if summary_parts else "No analysis results available"
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of all agents"""
        return {
            "agents": {
                name: {
                    "enabled": agent.enabled,
                    "model": agent.model,
                    "cost_per_1k": agent.cost_per_1k_tokens
                }
                for name, agent in self.agents.items()
            },
            "metrics": self.metrics,
            "settings": self.settings
        }
    
    def update_agent_settings(self, agent_name: str, settings: Dict[str, Any]):
        """Update settings for a specific agent"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            if "enabled" in settings:
                agent.enabled = settings["enabled"]
            if "model" in settings:
                agent.model = settings["model"]
                # Reinitialize LLM with new model
                from langchain_openai import ChatOpenAI
                agent.llm = ChatOpenAI(model=agent.model)
            logger.info(f"Updated settings for {agent_name} agent")
        else:
            logger.warning(f"Agent {agent_name} not found")
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False) 