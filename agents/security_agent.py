#!/usr/bin/env python3
"""
Security Scanner Agent
Analyzes code changes for potential security vulnerabilities
"""

import re
import json
from typing import Dict, Any, List
from agents.base_agent import SpecializedAgent, AgentState

# Security patterns to check
SECURITY_PATTERNS = {
    "hardcoded_secrets": [
        r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
        r"token\s*=\s*['\"][^'\"]+['\"]",
    ],
    "sql_injection": [
        r"execute\s*\(\s*['\"].*%s.*['\"].*%",
        r"cursor\.execute\s*\(\s*f['\"]",
        r"query\s*=\s*['\"].*\+.*['\"]",
    ],
    "unsafe_deserialization": [
        r"pickle\.loads?\s*\(",
        r"eval\s*\(",
        r"exec\s*\(",
    ],
    "insecure_random": [
        r"random\.\w+\s*\(",  # Using random instead of secrets
    ],
    "command_injection": [
        r"os\.system\s*\(",
        r"subprocess\.\w+\s*\([^,]+shell\s*=\s*True",
    ],
}

SECURITY_PROMPT = """You are a security expert analyzing code changes for potential vulnerabilities.

Commit: {commit_hash}
Message: {commit_message}

Code changes:
{git_diff}

Analyze the code changes for:
1. Security vulnerabilities (injection attacks, XSS, CSRF, etc.)
2. Hardcoded secrets or credentials
3. Insecure configurations
4. Authentication/authorization issues
5. Data exposure risks

Provide your analysis in JSON format:
{{
    "severity": "high|medium|low|none",
    "vulnerabilities": [
        {{
            "type": "vulnerability type",
            "description": "detailed description",
            "location": "file:line",
            "recommendation": "how to fix"
        }}
    ],
    "security_score": 0-100,
    "summary": "brief summary"
}}
"""


class SecurityAgent(SpecializedAgent):
    """Agent specialized in security analysis"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="security",
            prompt_template=SECURITY_PROMPT,
            cost_per_1k_tokens=0.01,  # GPT-4 turbo pricing
            **kwargs
        )
        
    def analyze(self, state: AgentState) -> AgentState:
        """Analyze code for security issues"""
        # First, do pattern-based analysis
        git_diff = state.get("git_diff", "")
        pattern_results = self._analyze_patterns(git_diff)
        
        # If patterns found issues or diff is substantial, use LLM
        if pattern_results["issues_found"] or len(git_diff) > 500:
            # Call parent analyze method for LLM analysis
            state = super().analyze(state)
            
            # Merge pattern results with LLM results
            if "agent_security" in state and "analysis" in state["agent_security"]:
                state["agent_security"]["pattern_analysis"] = pattern_results
        else:
            # Just use pattern analysis for small changes
            state = self.update_state(state, {
                "analysis": {
                    "severity": "none",
                    "vulnerabilities": [],
                    "security_score": 100,
                    "summary": "No security issues detected in pattern scan"
                },
                "pattern_analysis": pattern_results,
                "tokens_used": 0,
                "cost": 0
            })
            
        return state
    
    def _analyze_patterns(self, diff: str) -> Dict[str, Any]:
        """Quick pattern-based security analysis"""
        issues = []
        
        for category, patterns in SECURITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, diff, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    # Find line number in diff
                    line_num = diff[:match.start()].count('\n') + 1
                    issues.append({
                        "category": category,
                        "pattern": pattern,
                        "match": match.group(0),
                        "line": line_num
                    })
        
        return {
            "issues_found": len(issues) > 0,
            "pattern_matches": issues,
            "categories_triggered": list(set(issue["category"] for issue in issues))
        }
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process and validate security analysis response"""
        try:
            # Try to parse JSON response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response
                
            result = json.loads(json_str)
            
            # Validate expected fields
            if "severity" not in result:
                result["severity"] = "unknown"
            if "vulnerabilities" not in result:
                result["vulnerabilities"] = []
            if "security_score" not in result:
                result["security_score"] = 50
                
            return result
            
        except json.JSONDecodeError:
            # Fallback to raw response
            return {
                "raw_response": response,
                "severity": "unknown",
                "parsing_error": "Failed to parse JSON response"
            } 