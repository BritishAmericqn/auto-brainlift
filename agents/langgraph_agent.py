#!/usr/bin/env python3
"""
Auto-Brainlift LangGraph Agent
Generates context.md and brainlift.md from Git commits
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
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
        logging.FileHandler(log_dir / "langgraph_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GitCommitSummarizer:
    """Main agent for processing Git commits and generating summaries"""
    
    def __init__(self):
        # Initialize OpenAI
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
            temperature=0.7
        )
        
        # Set up directories
        # Use PROJECT_PATH from environment if available, otherwise use cwd
        project_path = os.getenv("PROJECT_PATH")
        if project_path:
            self.base_dir = Path(project_path)
        else:
            self.base_dir = Path.cwd()
        
        # Output directories should be relative to project
        self.output_dir = self.base_dir / "brainlifts"
        self.context_dir = self.base_dir / "context_logs"
        
        # Prompts are still relative to the script location
        script_dir = Path(__file__).parent.parent
        self.prompts_dir = script_dir / "prompts"
        
        # Ensure output directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.context_dir.mkdir(exist_ok=True)
        
        # Load prompt templates
        self.context_prompt = self._load_prompt("context.txt")
        self.brainlift_prompt = self._load_prompt("brainlift.txt")
        
        # Initialize the graph
        self.graph = self._build_graph()
        
    def _load_prompt(self, filename: str) -> str:
        """Load a prompt template from the prompts directory"""
        prompt_path = self.prompts_dir / filename
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt {filename}: {e}")
            raise
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(dict)
        
        # Define nodes
        workflow.add_node("parse_git_diff", self.parse_git_diff)
        workflow.add_node("summarize_context", self.summarize_context)
        workflow.add_node("summarize_brainlift", self.summarize_brainlift)
        workflow.add_node("write_output", self.write_output)
        
        # Define edges (linear flow)
        workflow.add_edge("parse_git_diff", "summarize_context")
        workflow.add_edge("summarize_context", "summarize_brainlift")
        workflow.add_edge("summarize_brainlift", "write_output")
        workflow.add_edge("write_output", END)
        
        # Set entry point
        workflow.set_entry_point("parse_git_diff")
        
        return workflow.compile()
    
    def parse_git_diff(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Git commit information and diff"""
        logger.info("Parsing Git diff...")
        
        try:
            # Get commit info from state or fetch latest
            if "commit_hash" in state:
                commit_hash = state["commit_hash"]
            else:
                # Get latest commit from current repo
                repo = git.Repo(self.base_dir)
                commit = repo.head.commit
                commit_hash = str(commit.hexsha)
            
            # Get commit details
            repo = git.Repo(self.base_dir)
            commit = repo.commit(commit_hash)
            
            # Get diff
            if commit.parents:
                diff = repo.git.diff(commit.parents[0].hexsha, commit.hexsha)
            else:
                # First commit
                diff = repo.git.show(commit.hexsha)
            
            # Extract commit info
            commit_info = {
                "commit_hash": f"Commit: {commit.hexsha[:8]}",
                "commit_message": f"Message: {commit.message.strip()}",
                "commit_author": f"Author: {commit.author.name} <{commit.author.email}>",
                "commit_date": f"Date: {datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S')}",
                "git_diff": diff[:5000]  # Limit diff size
            }
            
            state.update(commit_info)
            logger.info(f"Parsed commit: {commit.hexsha[:8]}")
            
        except Exception as e:
            logger.error(f"Error parsing Git diff: {e}")
            raise
        
        return state
    
    def summarize_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate context.md summary"""
        logger.info("Generating context summary...")
        
        try:
            # Format the prompt
            prompt = self.context_prompt.format(**state)
            
            # Log the prompt for debugging
            logger.debug(f"Context prompt: {prompt[:200]}...")
            
            # Generate summary
            response = self.llm.invoke([HumanMessage(content=prompt)])
            context_summary = response.content
            
            state["context_summary"] = context_summary
            logger.info("Context summary generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating context summary: {e}")
            raise
        
        return state
    
    def summarize_brainlift(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brainlift.md summary"""
        logger.info("Generating brainlift summary...")
        
        try:
            # Format the prompt
            prompt = self.brainlift_prompt.format(**state)
            
            # Log the prompt for debugging
            logger.debug(f"Brainlift prompt: {prompt[:200]}...")
            
            # Generate summary
            response = self.llm.invoke([HumanMessage(content=prompt)])
            brainlift_summary = response.content
            
            state["brainlift_summary"] = brainlift_summary
            logger.info("Brainlift summary generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating brainlift summary: {e}")
            raise
        
        return state
    
    def write_output(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Write both summaries to their respective files"""
        logger.info("Writing output files...")
        
        try:
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Write context.md
            context_path = self.context_dir / f"{timestamp}_context.md"
            with open(context_path, 'w') as f:
                f.write(state["context_summary"])
            logger.info(f"Wrote context log: {context_path}")
            
            # Write brainlift.md
            brainlift_path = self.output_dir / f"{timestamp}_brainlift.md"
            with open(brainlift_path, 'w') as f:
                f.write(state["brainlift_summary"])
            logger.info(f"Wrote brainlift: {brainlift_path}")
            
            state["output_files"] = {
                "context": str(context_path),
                "brainlift": str(brainlift_path)
            }
            
        except Exception as e:
            logger.error(f"Error writing output files: {e}")
            raise
        
        return state
    
    def process_commit(self, commit_hash: str = None) -> Dict[str, Any]:
        """Process a Git commit and generate summaries"""
        initial_state = {}
        if commit_hash:
            initial_state["commit_hash"] = commit_hash
        
        try:
            result = self.graph.invoke(initial_state)
            logger.info("Successfully processed commit")
            return result
        except Exception as e:
            logger.error(f"Error processing commit: {e}")
            raise


def main():
    """Main entry point for testing"""
    import sys
    
    # Get commit hash from command line if provided
    commit_hash = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        summarizer = GitCommitSummarizer()
        result = summarizer.process_commit(commit_hash)
        
        print("\n✅ Summary generation complete!")
        print(f"Context log: {result['output_files']['context']}")
        print(f"Brainlift: {result['output_files']['brainlift']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Failed to generate summaries: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 