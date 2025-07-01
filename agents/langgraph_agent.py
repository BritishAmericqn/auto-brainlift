#!/usr/bin/env python3
"""
Auto-Brainlift LangGraph Agent
Generates context.md and brainlift.md from Git commits
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import git

# Import cache and budget managers
from cache import CacheManager
from budget_manager import BudgetManager
from agent_orchestrator import AgentOrchestrator

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
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.7
        )
        
        # Set up directories
        # Use PROJECT_PATH from environment if available, otherwise use cwd
        project_path = os.getenv("PROJECT_PATH")
        if project_path:
            self.base_dir = Path(project_path)
        else:
            self.base_dir = Path.cwd()
        
        # Get project name from environment
        self.project_name = os.getenv("PROJECT_NAME", self.base_dir.name)
        
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
        
        # Initialize cache and budget managers
        self._init_cache_and_budget()
        
        # Initialize agent orchestrator for multi-agent analysis
        self.agent_orchestrator = None
        self._init_agent_orchestrator()
        
        # Initialize the graph
        self.graph = self._build_graph()
    
    def _init_cache_and_budget(self):
        """Initialize cache and budget managers"""
        try:
            # Get project ID from environment or generate from path
            project_id = os.getenv("PROJECT_ID")
            if not project_id:
                # Use a hash of the project path as ID
                import hashlib
                project_id = hashlib.md5(str(self.base_dir).encode()).hexdigest()[:12]
            
            # Initialize cache manager
            self.cache_manager = CacheManager(project_id)
            logger.info(f"Initialized cache manager for project {project_id}")
            
            # Get project settings from environment
            settings = {
                'budgetEnabled': os.getenv('BUDGET_ENABLED', 'false').lower() == 'true',
                'commitTokenLimit': int(os.getenv('COMMIT_TOKEN_LIMIT', '10000'))
            }
            
            # Initialize budget manager
            self.budget_manager = BudgetManager(project_id, settings)
            logger.info(f"Initialized budget manager with settings: {settings}")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache/budget managers: {e}")
            # Create dummy managers that don't cache/track
            self.cache_manager = None
            self.budget_manager = None
    
    def _init_agent_orchestrator(self):
        """Initialize the agent orchestrator for multi-agent analysis"""
        try:
            # Get project ID and settings
            project_id = os.getenv("PROJECT_ID")
            if not project_id:
                import hashlib
                project_id = hashlib.md5(str(self.base_dir).encode()).hexdigest()[:12]
            
            # Get agent settings from environment or defaults
            agent_settings = {
                'budgetEnabled': os.getenv('BUDGET_ENABLED', 'false').lower() == 'true',
                'commitTokenLimit': int(os.getenv('COMMIT_TOKEN_LIMIT', '10000')),
                'execution_mode': os.getenv('AGENT_EXECUTION_MODE', 'parallel'),
                'agents': {
                    'security': {
                        'enabled': os.getenv('SECURITY_AGENT_ENABLED', 'true').lower() == 'true',
                        'model': os.getenv('SECURITY_AGENT_MODEL', 'gpt-4-turbo')
                    },
                    'quality': {
                        'enabled': os.getenv('QUALITY_AGENT_ENABLED', 'true').lower() == 'true',
                        'model': os.getenv('QUALITY_AGENT_MODEL', 'gpt-4-turbo')
                    },
                    'documentation': {
                        'enabled': os.getenv('DOCUMENTATION_AGENT_ENABLED', 'true').lower() == 'true',
                        'model': os.getenv('DOCUMENTATION_AGENT_MODEL', 'gpt-4-turbo')
                    }
                }
            }
            
            # Initialize orchestrator
            self.agent_orchestrator = AgentOrchestrator(project_id, agent_settings)
            logger.info(f"Initialized agent orchestrator for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent orchestrator: {e}")
            self.agent_orchestrator = None
        
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
        workflow.add_node("check_cache_and_budget", self.check_cache_and_budget)
        workflow.add_node("run_multi_agents", self.run_multi_agents)
        workflow.add_node("summarize_context", self.summarize_context)
        workflow.add_node("summarize_brainlift", self.summarize_brainlift)
        workflow.add_node("write_output", self.write_output)
        
        # Define edges (linear flow with cache check and multi-agent analysis)
        workflow.add_edge("parse_git_diff", "check_cache_and_budget")
        workflow.add_edge("check_cache_and_budget", "run_multi_agents")
        workflow.add_edge("run_multi_agents", "summarize_context")
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
                "commit_hash": commit.hexsha,  # Store full hash
                "commit_hash_display": f"Commit: {commit.hexsha[:8]}",
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
    
    def run_multi_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run multi-agent analysis if enabled"""
        logger.info("Running multi-agent analysis...")
        
        # Check if multi-agent analysis is enabled
        if not self.agent_orchestrator:
            logger.info("Multi-agent analysis not enabled, skipping")
            return state
        
        # Skip if already cached
        if state.get('cache_hit', False):
            logger.info("Using cached results, skipping multi-agent analysis")
            return state
        
        try:
            # Get commit info
            commit_info = {
                "commit_hash": state.get("commit_hash", ""),
                "commit_message": state.get("commit_message", ""),
                "commit_author": state.get("commit_author", ""),
                "commit_date": state.get("commit_date", "")
            }
            
            # Run multi-agent analysis
            agent_results = self.agent_orchestrator.analyze_commit(
                state.get("git_diff", ""),
                commit_info
            )
            
            # Store results in state
            state["multi_agent_results"] = agent_results
            
            # Add agent insights to the context for summary generation
            if agent_results.get("summary"):
                state["agent_insights"] = agent_results["summary"]
                
            logger.info(f"Multi-agent analysis complete: {agent_results.get('summary', 'No summary')}")
            
        except Exception as e:
            logger.error(f"Error in multi-agent analysis: {e}")
            state["multi_agent_error"] = str(e)
            
        return state
    
    def check_cache_and_budget(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Check cache for existing results and validate budget"""
        logger.info("Checking cache and budget...")
        
        # Skip if managers not initialized
        if not self.cache_manager or not self.budget_manager:
            logger.warning("Cache/budget managers not available, skipping checks")
            return state
        
        try:
            # Create cache key from commit hash for more stable caching
            cache_key = f"commit_with_agents:{state.get('commit_hash', 'unknown')}"
            
            # Estimate tokens for budget check
            estimated_tokens = self.budget_manager.estimate_tokens(state.get("git_diff", ""))
            
            # Check budget
            within_budget, budget_details = self.budget_manager.check_budget(
                estimated_tokens, 
                self.model
            )
            
            state['budget_check'] = budget_details
            
            if not within_budget and budget_details['budget_enabled']:
                logger.warning(f"Budget exceeded: {budget_details}")
                # Continue with warning
            
            # Only check cache, don't generate summaries here
            # The summaries will be generated after multi-agent analysis
            cached_result = self.cache_manager.exact_cache.get(cache_key)
            
            if cached_result is not None:
                logger.info(f"Cache hit for commit with agents")
                state['cache_hit'] = True
                # Restore all cached data including agent results
                state['context_summary'] = cached_result.get('context_summary', '')
                state['brainlift_summary'] = cached_result.get('brainlift_summary', '')
                state['multi_agent_results'] = cached_result.get('multi_agent_results', {})
            else:
                logger.info("Cache miss - will generate new summaries with agent analysis")
                state['cache_hit'] = False
                state['cache_key'] = cache_key  # Store for later caching
                
            # Log cache stats
            stats = self.cache_manager.get_cache_stats()
            logger.info(f"Cache stats: {stats['overall']}")
                
        except Exception as e:
            logger.error(f"Error in cache/budget check: {e}")
            state['cache_hit'] = False
            
        return state
    
    def summarize_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate context.md summary"""
        # Check if we already have a cached result in state
        if state.get('context_summary'):
            logger.info("Using cached context summary")
            return state
            
        logger.info("Generating context summary...")
        
        try:
            # Build agent analysis section if available
            agent_analysis = ""
            if state.get("multi_agent_results"):
                results = state["multi_agent_results"]
                agent_analysis = "\n\n## Multi-Agent Analysis Results:\n"
                
                # Add overall summary
                if results.get("summary"):
                    agent_analysis += f"\n**Overall Assessment:** {results['summary']}\n"
                
                # Add individual agent results
                if results.get("agents"):
                    for agent_name, agent_data in results["agents"].items():
                        if "error" not in agent_data and "analysis" in agent_data:
                            analysis = agent_data["analysis"]
                            agent_analysis += f"\n### {agent_name.title()} Analysis:\n"
                            
                            if agent_name == "security":
                                agent_analysis += f"- Security Score: {analysis.get('security_score', 'N/A')}/100\n"
                                agent_analysis += f"- Severity: {analysis.get('severity', 'none')}\n"
                                if analysis.get('vulnerabilities'):
                                    agent_analysis += f"- Found {len(analysis['vulnerabilities'])} potential issues\n"
                                    
                            elif agent_name == "quality":
                                agent_analysis += f"- Quality Score: {analysis.get('quality_score', 'N/A')}/100\n"
                                agent_analysis += f"- Complexity: {analysis.get('complexity', 'N/A')}\n"
                                if analysis.get('issues'):
                                    agent_analysis += f"- Found {len(analysis['issues'])} quality issues\n"
                                    
                            elif agent_name == "documentation":
                                agent_analysis += f"- Documentation Score: {analysis.get('documentation_score', 'N/A')}/100\n"
                                agent_analysis += f"- Coverage: {analysis.get('coverage', 'N/A')}%\n"
                                if analysis.get('missing'):
                                    agent_analysis += f"- Missing docs for {len(analysis['missing'])} items\n"
            
            # Format the prompt with agent analysis appended
            prompt = self.context_prompt.format(
                commit_hash=state.get("commit_hash_display", ""),
                commit_message=state.get("commit_message", ""),
                commit_author=state.get("commit_author", ""),
                commit_date=state.get("commit_date", ""),
                git_diff=state.get("git_diff", "")
            )
            
            # Append agent analysis to the prompt
            if agent_analysis:
                prompt += agent_analysis
            
            # Log the prompt for debugging
            logger.debug(f"Context prompt: {prompt[:200]}...")
            
            # Generate summary
            response = self.llm.invoke([HumanMessage(content=prompt)])
            context_summary = response.content
            
            # Track token usage
            if self.budget_manager:
                tokens_used = len(prompt) // 4 + len(context_summary) // 4
                self.budget_manager.record_usage(
                    tokens_used,
                    self.model,
                    state.get("commit_hash", None)
                )
                logger.info(f"Recorded {tokens_used} tokens for context summary")
            
            state["context_summary"] = context_summary
            logger.info("Context summary generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating context summary: {e}")
            raise
        
        return state
    
    def summarize_brainlift(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brainlift.md summary"""
        # Check if we already have a cached result in state
        if state.get('brainlift_summary'):
            logger.info("Using cached brainlift summary")
            return state
            
        logger.info("Generating brainlift summary...")
        
        try:
            # Build agent insights narrative if available
            agent_insights = ""
            if state.get("multi_agent_results"):
                results = state["multi_agent_results"]
                agent_insights = "\n\n## Automated Analysis Insights:\n"
                
                # Add narrative insights from each agent
                if results.get("agents"):
                    for agent_name, agent_data in results["agents"].items():
                        if "error" not in agent_data and "analysis" in agent_data:
                            analysis = agent_data["analysis"]
                            
                            if agent_name == "security" and analysis.get("vulnerabilities"):
                                agent_insights += f"\n**Security Considerations:** "
                                if analysis.get("severity") != "none":
                                    agent_insights += f"The security scan found {analysis['severity']} severity issues that need attention. "
                                agent_insights += "Consider reviewing the security vulnerabilities identified in this commit.\n"
                                
                            elif agent_name == "quality":
                                score = analysis.get("quality_score", 0)
                                if score < 70:
                                    agent_insights += f"\n**Code Quality:** The code quality score of {score}/100 suggests there's room for improvement. "
                                    agent_insights += "Consider refactoring for better maintainability.\n"
                                elif score >= 85:
                                    agent_insights += f"\n**Code Quality:** Excellent code quality score of {score}/100! "
                                    agent_insights += "The code follows best practices well.\n"
                                    
                            elif agent_name == "documentation":
                                doc_score = analysis.get("documentation_score", 0)
                                if doc_score < 50:
                                    agent_insights += f"\n**Documentation:** With a documentation score of {doc_score}/100, "
                                    agent_insights += "this code could benefit from better documentation. Consider adding more comments and docstrings.\n"
            
            # Format the prompt
            prompt = self.brainlift_prompt.format(
                commit_hash=state.get("commit_hash_display", ""),
                commit_message=state.get("commit_message", ""),
                commit_author=state.get("commit_author", ""),
                commit_date=state.get("commit_date", ""),
                git_diff=state.get("git_diff", "")
            )
            
            # Append agent insights to make the brainlift more insightful
            if agent_insights:
                prompt += agent_insights
            
            # Log the prompt for debugging
            logger.debug(f"Brainlift prompt: {prompt[:200]}...")
            
            # Generate summary
            response = self.llm.invoke([HumanMessage(content=prompt)])
            brainlift_summary = response.content
            
            # Track token usage
            if self.budget_manager:
                tokens_used = len(prompt) // 4 + len(brainlift_summary) // 4
                self.budget_manager.record_usage(
                    tokens_used,
                    self.model,
                    state.get("commit_hash", None)
                )
                logger.info(f"Recorded {tokens_used} tokens for brainlift summary")
            
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
            
            # Cache the complete results including multi-agent analysis
            if self.cache_manager and state.get('cache_key') and not state.get('cache_hit'):
                cache_data = {
                    'context_summary': state.get('context_summary', ''),
                    'brainlift_summary': state.get('brainlift_summary', ''),
                    'multi_agent_results': state.get('multi_agent_results', {}),
                    'output_files': state['output_files']
                }
                self.cache_manager.exact_cache.set(
                    state['cache_key'],
                    cache_data,
                    ttl=86400  # 24 hours
                )
                logger.info(f"Cached results with multi-agent analysis")
            
            # Log final stats
            if self.cache_manager:
                stats = self.cache_manager.get_cache_stats()
                logger.info(f"Final cache stats: Hit rate: {stats['overall']['hit_rate']:.2%}, Total requests: {stats['overall']['total_requests']}")
            
            if self.budget_manager:
                usage_summary = self.budget_manager.get_usage_summary()
                logger.info(f"Token usage - Today: {usage_summary['today']['tokens']} tokens (${usage_summary['today']['cost']:.4f})")
            
        except Exception as e:
            logger.error(f"Error writing output files: {e}")
            raise
        
        return state
    
    def process_commit(self, commit_hash: Optional[str] = None) -> Dict[str, Any]:
        """Process a Git commit and generate summaries"""
        initial_state = {}
        if commit_hash:
            initial_state["commit_hash"] = commit_hash
        
        try:
            # Quick cache check before running full workflow
            if self.cache_manager:
                # Get commit info for cache key
                repo = git.Repo(self.base_dir)
                commit = repo.commit(commit_hash) if commit_hash else repo.head.commit
                
                # Create a more stable cache key using commit hash instead of diff
                cache_key = f"commit:{commit.hexsha}"
                
                # Check if we have this commit cached
                cached = self.cache_manager.exact_cache.get(cache_key)
                
                if cached is not None:
                    logger.info(f"Quick cache hit for commit {commit.hexsha[:8]}")
                    # Return early with cached data
                    return {
                        'cache_hit': True,
                        'output_files': cached.get('output_files', {}),
                        'context_summary': cached.get('context_summary', ''),
                        'brainlift_summary': cached.get('brainlift_summary', ''),
                        'budget_check': {
                            'estimated_tokens': 0,
                            'estimated_cost': 0.0
                        }
                    }
            
            # Run full workflow if not cached
            result = self.graph.invoke(initial_state)
            
            # Cache the result using commit hash as key
            if self.cache_manager and result.get('output_files'):
                cache_data = {
                    'output_files': result['output_files'],
                    'context_summary': result.get('context_summary', ''),
                    'brainlift_summary': result.get('brainlift_summary', '')
                }
                self.cache_manager.exact_cache.set(
                    cache_key,
                    cache_data,
                    ttl=86400  # 24 hours for commit-based cache
                )
            
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
        
        if result.get('cache_hit'):
            print("📦 Result was served from cache!")
        
        if result.get('budget_check'):
            print(f"💰 Token estimate: {result['budget_check']['estimated_tokens']}")
            print(f"💵 Cost estimate: ${result['budget_check']['estimated_cost']:.4f}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Failed to generate summaries: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 