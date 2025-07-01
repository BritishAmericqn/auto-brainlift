#!/usr/bin/env python3
"""
Code Quality Analyzer Agent
Analyzes code changes for quality issues, best practices, and maintainability
"""

import re
import json
from typing import Dict, Any, List
from agents.base_agent import SpecializedAgent, AgentState

# Code quality patterns to check
QUALITY_PATTERNS = {
    "long_functions": {
        "pattern": r"def\s+\w+\s*\([^)]*\):[^\n]*\n(?:.*\n){50,}",
        "message": "Function appears to be very long (50+ lines)"
    },
    "complex_conditions": {
        "pattern": r"if\s+[^:]+(?:and|or)[^:]+(?:and|or)[^:]+:",
        "message": "Complex conditional with multiple and/or operators"
    },
    "magic_numbers": {
        "pattern": r"(?<!['\"])\b(?:86400|3600|1024|255|100|1000)\b(?!['\"])",
        "message": "Magic number detected - consider using named constant"
    },
    "todo_fixme": {
        "pattern": r"#\s*(?:TODO|FIXME|HACK|XXX)",
        "message": "TODO/FIXME comment found"
    },
    "print_statements": {
        "pattern": r"^\s*print\s*\(",
        "message": "Print statement found - consider using logging"
    },
    "bare_except": {
        "pattern": r"except\s*:",
        "message": "Bare except clause - should catch specific exceptions"
    },
}

QUALITY_PROMPT = """You are a code quality expert analyzing code changes for best practices and maintainability.

Commit: {commit_hash}
Message: {commit_message}

Code changes:
{git_diff}

Analyze the code changes for:
1. Code complexity and readability
2. Adherence to best practices (DRY, SOLID, etc.)
3. Error handling quality
4. Documentation and comments
5. Test coverage implications
6. Performance considerations
7. Maintainability concerns

Provide your analysis in JSON format:
{{
    "quality_score": 0-100,
    "issues": [
        {{
            "type": "issue type",
            "severity": "high|medium|low",
            "description": "detailed description",
            "location": "file:line",
            "suggestion": "improvement suggestion"
        }}
    ],
    "metrics": {{
        "complexity": "low|medium|high",
        "readability": "good|fair|poor",
        "maintainability": "high|medium|low"
    }},
    "positive_aspects": ["list of good practices observed"],
    "summary": "brief summary"
}}
"""


class QualityAgent(SpecializedAgent):
    """Agent specialized in code quality analysis"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="quality",
            prompt_template=QUALITY_PROMPT,
            cost_per_1k_tokens=0.01,  # GPT-4 turbo pricing
            **kwargs
        )
        
    def analyze(self, state: AgentState) -> AgentState:
        """Analyze code for quality issues"""
        # First, do pattern-based analysis
        git_diff = state.get("git_diff", "")
        pattern_results = self._analyze_patterns(git_diff)
        
        # Calculate quick metrics
        metrics = self._calculate_metrics(git_diff)
        
        # If patterns found issues or diff is substantial, use LLM
        if pattern_results["issues_found"] > 2 or len(git_diff) > 500:
            # Call parent analyze method for LLM analysis
            state = super().analyze(state)
            
            # Merge pattern results with LLM results
            if "agent_quality" in state and "analysis" in state["agent_quality"]:
                state["agent_quality"]["pattern_analysis"] = pattern_results
                state["agent_quality"]["quick_metrics"] = metrics
        else:
            # Just use pattern analysis for small changes
            state = self.update_state(state, {
                "analysis": {
                    "quality_score": 100 - (pattern_results["issues_found"] * 10),
                    "issues": pattern_results["issues"],
                    "metrics": metrics,
                    "positive_aspects": [],
                    "summary": f"Quick analysis found {pattern_results['issues_found']} potential issues"
                },
                "pattern_analysis": pattern_results,
                "quick_metrics": metrics,
                "tokens_used": 0,
                "cost": 0
            })
            
        return state
    
    def _analyze_patterns(self, diff: str) -> Dict[str, Any]:
        """Quick pattern-based quality analysis"""
        issues = []
        
        for check_name, check_data in QUALITY_PATTERNS.items():
            pattern = check_data["pattern"]
            matches = re.finditer(pattern, diff, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Find line number in diff
                line_num = diff[:match.start()].count('\n') + 1
                issues.append({
                    "type": check_name,
                    "severity": "medium" if check_name in ["bare_except", "long_functions"] else "low",
                    "description": check_data["message"],
                    "location": f"line:{line_num}",
                    "match": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                })
        
        return {
            "issues_found": len(issues),
            "issues": issues,
            "checks_triggered": list(set(issue["type"] for issue in issues))
        }
    
    def _calculate_metrics(self, diff: str) -> Dict[str, str]:
        """Calculate quick code metrics"""
        lines = diff.split('\n')
        
        # Count various elements
        added_lines = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        comment_lines = sum(1 for line in lines if line.strip().startswith('#') and line.startswith('+'))
        
        # Simple complexity estimation
        complexity_indicators = sum(1 for line in lines if any(keyword in line for keyword in ['if', 'for', 'while', 'try']))
        
        # Determine ratings
        complexity = "high" if complexity_indicators > 10 else "medium" if complexity_indicators > 5 else "low"
        readability = "poor" if added_lines > 100 else "fair" if added_lines > 50 else "good"
        comment_ratio = comment_lines / max(added_lines, 1)
        maintainability = "high" if comment_ratio > 0.1 else "medium" if comment_ratio > 0.05 else "low"
        
        return {
            "complexity": complexity,
            "readability": readability,
            "maintainability": maintainability,
            "added_lines": str(added_lines),
            "comment_ratio": f"{comment_ratio:.2%}"
        }
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process and validate quality analysis response"""
        try:
            # Try to parse JSON response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response
                
            result = json.loads(json_str)
            
            # Validate expected fields with defaults
            if "quality_score" not in result:
                result["quality_score"] = 70
            if "issues" not in result:
                result["issues"] = []
            if "metrics" not in result:
                result["metrics"] = {
                    "complexity": "medium",
                    "readability": "fair",
                    "maintainability": "medium"
                }
            if "positive_aspects" not in result:
                result["positive_aspects"] = []
                
            return result
            
        except json.JSONDecodeError:
            # Fallback to raw response
            return {
                "raw_response": response,
                "quality_score": 50,
                "parsing_error": "Failed to parse JSON response"
            } 