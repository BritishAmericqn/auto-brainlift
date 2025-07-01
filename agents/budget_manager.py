"""
Budget manager for tracking token usage and costs
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BudgetManager:
    """Manages token budgets and tracks usage per project"""
    
    def __init__(self, project_id: str, settings: Dict[str, Any], cache_dir: Optional[Path] = None):
        self.project_id = project_id
        self.settings = settings
        
        # Set up budget directory to match Electron's app.getPath('userData')
        if cache_dir is None:
            # Use platform-specific app data directory
            import platform
            if platform.system() == 'Darwin':  # macOS
                cache_dir = Path.home() / 'Library' / 'Application Support' / 'auto-brainlift' / 'projects'
            elif platform.system() == 'Windows':
                cache_dir = Path.home() / 'AppData' / 'Roaming' / 'auto-brainlift' / 'projects'
            else:  # Linux
                cache_dir = Path.home() / '.config' / 'auto-brainlift' / 'projects'
        
        self.budget_dir = cache_dir / project_id / 'budget'
        self.budget_dir.mkdir(parents=True, exist_ok=True)
        
        self.usage_file = self.budget_dir / 'usage.json'
        
        # Model pricing (per 1K tokens)
        self.model_costs = {
            'gpt-4': 0.03,
            'gpt-4-turbo': 0.01,
            'gpt-3.5-turbo': 0.0015,
            'text-embedding-ada-002': 0.0001
        }
        
        # Load existing usage data
        self.usage_data = self._load_usage()
    
    def _load_usage(self) -> Dict[str, Any]:
        """Load usage data from disk"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load usage data: {e}")
        
        # Initialize with empty data
        return {
            'total_tokens': 0,
            'total_cost': 0.0,
            'commits': {},
            'daily_usage': {},
            'model_breakdown': {}
        }
    
    def _save_usage(self) -> None:
        """Save usage data to disk"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def check_budget(self, estimated_tokens: int, model: str = 'gpt-4-turbo') -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within budget
        
        Returns:
            Tuple of (within_budget, details)
        """
        # Get settings
        budget_enabled = self.settings.get('budgetEnabled', False)
        commit_limit = self.settings.get('commitTokenLimit', 10000)
        
        # Calculate estimated cost
        estimated_cost = self.calculate_cost(estimated_tokens, model)
        
        # If budget is disabled, always allow (but still track)
        if not budget_enabled:
            return True, {
                'budget_enabled': False,
                'estimated_tokens': estimated_tokens,
                'estimated_cost': estimated_cost,
                'message': 'Budget checking disabled'
            }
        
        # Check against per-commit limit
        within_budget = estimated_tokens <= commit_limit
        
        return within_budget, {
            'budget_enabled': True,
            'within_budget': within_budget,
            'estimated_tokens': estimated_tokens,
            'commit_limit': commit_limit,
            'estimated_cost': estimated_cost,
            'message': f"{'Within' if within_budget else 'Exceeds'} budget limit"
        }
    
    def record_usage(self, tokens_used: int, model: str, commit_hash: Optional[str] = None) -> None:
        """Record actual token usage"""
        cost = self.calculate_cost(tokens_used, model)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Update totals
        self.usage_data['total_tokens'] += tokens_used
        self.usage_data['total_cost'] += cost
        
        # Update daily usage
        if today not in self.usage_data['daily_usage']:
            self.usage_data['daily_usage'][today] = {
                'tokens': 0,
                'cost': 0.0
            }
        
        self.usage_data['daily_usage'][today]['tokens'] += tokens_used
        self.usage_data['daily_usage'][today]['cost'] += cost
        
        # Update model breakdown
        if model not in self.usage_data['model_breakdown']:
            self.usage_data['model_breakdown'][model] = {
                'tokens': 0,
                'cost': 0.0
            }
        
        self.usage_data['model_breakdown'][model]['tokens'] += tokens_used
        self.usage_data['model_breakdown'][model]['cost'] += cost
        
        # Record commit-specific usage if provided
        if commit_hash:
            self.usage_data['commits'][commit_hash] = {
                'tokens': tokens_used,
                'cost': cost,
                'model': model,
                'timestamp': time.time()
            }
        
        # Save to disk
        self._save_usage()
        
        logger.info(f"Recorded usage: {tokens_used} tokens, ${cost:.4f} for model {model}")
    
    def calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost for given tokens and model"""
        cost_per_1k = self.model_costs.get(model, 0.01)  # Default to GPT-4-turbo pricing
        return (tokens / 1000) * cost_per_1k
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary"""
        # Calculate period summaries
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        today_usage = self.usage_data['daily_usage'].get(today, {'tokens': 0, 'cost': 0.0})
        
        # Calculate weekly totals
        week_tokens = 0
        week_cost = 0.0
        for date, usage in self.usage_data['daily_usage'].items():
            if date >= week_ago:
                week_tokens += usage['tokens']
                week_cost += usage['cost']
        
        # Calculate monthly totals
        month_tokens = 0
        month_cost = 0.0
        for date, usage in self.usage_data['daily_usage'].items():
            if date >= month_ago:
                month_tokens += usage['tokens']
                month_cost += usage['cost']
        
        return {
            'total': {
                'tokens': self.usage_data['total_tokens'],
                'cost': self.usage_data['total_cost']
            },
            'today': today_usage,
            'week': {
                'tokens': week_tokens,
                'cost': week_cost
            },
            'month': {
                'tokens': month_tokens,
                'cost': month_cost
            },
            'by_model': self.usage_data['model_breakdown'],
            'recent_commits': list(self.usage_data['commits'].items())[-10:]  # Last 10 commits
        }
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        Uses simple heuristic: ~4 characters per token
        """
        # More accurate estimation based on OpenAI's guidelines
        # Average: ~4 characters per token for English text
        # Adjust for code (more tokens due to symbols)
        if self._looks_like_code(text):
            return len(text) // 3  # Code uses more tokens
        else:
            return len(text) // 4  # Regular text
    
    def _looks_like_code(self, text: str) -> bool:
        """Simple heuristic to detect if text looks like code"""
        code_indicators = ['{', '}', '()', '=>', 'function', 'class', 'def', 'import']
        indicator_count = sum(1 for ind in code_indicators if ind in text)
        return indicator_count >= 3
    
    def reset_usage(self, period: str = 'all') -> None:
        """Reset usage data for specified period"""
        if period == 'all':
            self.usage_data = {
                'total_tokens': 0,
                'total_cost': 0.0,
                'commits': {},
                'daily_usage': {},
                'model_breakdown': {}
            }
        elif period == 'daily':
            today = datetime.now().strftime('%Y-%m-%d')
            if today in self.usage_data['daily_usage']:
                del self.usage_data['daily_usage'][today]
        
        self._save_usage()
        logger.info(f"Reset usage data for period: {period}") 