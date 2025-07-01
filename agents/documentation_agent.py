#!/usr/bin/env python3
"""
Documentation Generator Agent
Analyzes code changes and generates appropriate documentation
"""

import re
import json
from typing import Dict, Any, List
from agents.base_agent import SpecializedAgent, AgentState

DOCUMENTATION_PROMPT = """You are a technical documentation expert analyzing code changes to generate helpful documentation.

Commit: {commit_hash}
Message: {commit_message}

Code changes:
{git_diff}

Analyze the code changes and generate:
1. Function/method documentation (docstrings)
2. Module/class documentation
3. API documentation for public interfaces
4. README updates if needed
5. Changelog entries
6. Code comments for complex logic

Provide your analysis in JSON format:
{{
    "documentation_score": 0-100,
    "missing_docs": [
        {{
            "type": "function|class|module",
            "name": "identifier name",
            "location": "file:line",
            "suggested_doc": "suggested documentation"
        }}
    ],
    "suggested_readme_updates": ["list of suggested updates"],
    "changelog_entry": "suggested changelog entry",
    "inline_comments_needed": [
        {{
            "location": "file:line",
            "reason": "why comment is needed",
            "suggestion": "suggested comment"
        }}
    ],
    "existing_docs_quality": "good|fair|poor",
    "summary": "brief summary"
}}
"""


class DocumentationAgent(SpecializedAgent):
    """Agent specialized in documentation generation and analysis"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="documentation",
            prompt_template=DOCUMENTATION_PROMPT,
            cost_per_1k_tokens=0.01,  # GPT-4 turbo pricing
            **kwargs
        )
        
    def analyze(self, state: AgentState) -> AgentState:
        """Analyze code and generate documentation suggestions"""
        git_diff = state.get("git_diff", "")
        
        # Quick analysis of documentation coverage
        doc_analysis = self._analyze_documentation_coverage(git_diff)
        
        # If significant undocumented code or large diff, use LLM
        if doc_analysis["undocumented_items"] > 2 or len(git_diff) > 500:
            # Call parent analyze method for LLM analysis
            state = super().analyze(state)
            
            # Merge quick analysis with LLM results
            if "agent_documentation" in state and "analysis" in state["agent_documentation"]:
                state["agent_documentation"]["quick_analysis"] = doc_analysis
        else:
            # Generate basic documentation suggestions
            suggestions = self._generate_basic_suggestions(git_diff, doc_analysis)
            
            state = self.update_state(state, {
                "analysis": suggestions,
                "quick_analysis": doc_analysis,
                "tokens_used": 0,
                "cost": 0
            })
            
        return state
    
    def _analyze_documentation_coverage(self, diff: str) -> Dict[str, Any]:
        """Quick analysis of documentation coverage in diff"""
        lines = diff.split('\n')
        
        # Patterns for various code elements
        function_pattern = r'^\+\s*def\s+(\w+)\s*\('
        class_pattern = r'^\+\s*class\s+(\w+)'
        docstring_pattern = r'^\+\s*"""'
        comment_pattern = r'^\+\s*#'
        
        functions = []
        classes = []
        docstrings = 0
        comments = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for functions
            func_match = re.match(function_pattern, line)
            if func_match:
                func_name = func_match.group(1)
                # Check if next line has docstring
                has_docstring = (i + 1 < len(lines) and 
                               ('"""' in lines[i + 1] or "'''" in lines[i + 1]))
                functions.append({
                    "name": func_name,
                    "line": i + 1,
                    "has_docstring": has_docstring
                })
            
            # Check for classes
            class_match = re.match(class_pattern, line)
            if class_match:
                class_name = class_match.group(1)
                # Check if next line has docstring
                has_docstring = (i + 1 < len(lines) and 
                               ('"""' in lines[i + 1] or "'''" in lines[i + 1]))
                classes.append({
                    "name": class_name,
                    "line": i + 1,
                    "has_docstring": has_docstring
                })
            
            # Count docstrings and comments
            if re.match(docstring_pattern, line):
                docstrings += 1
            if re.match(comment_pattern, line):
                comments += 1
                
            i += 1
        
        undocumented_functions = [f for f in functions if not f["has_docstring"]]
        undocumented_classes = [c for c in classes if not c["has_docstring"]]
        
        return {
            "functions_found": len(functions),
            "classes_found": len(classes),
            "undocumented_functions": undocumented_functions,
            "undocumented_classes": undocumented_classes,
            "undocumented_items": len(undocumented_functions) + len(undocumented_classes),
            "docstrings_found": docstrings,
            "comments_found": comments,
            "documentation_ratio": (docstrings + comments) / max(len(functions) + len(classes), 1)
        }
    
    def _generate_basic_suggestions(self, diff: str, doc_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic documentation suggestions without LLM"""
        missing_docs = []
        
        # Suggest docs for undocumented functions
        for func in doc_analysis["undocumented_functions"]:
            missing_docs.append({
                "type": "function",
                "name": func["name"],
                "location": f"line:{func['line']}",
                "suggested_doc": f'"""TODO: Add description for {func["name"]}.\n\nArgs:\n    TODO\n\nReturns:\n    TODO\n"""'
            })
        
        # Suggest docs for undocumented classes
        for cls in doc_analysis["undocumented_classes"]:
            missing_docs.append({
                "type": "class",
                "name": cls["name"],
                "location": f"line:{cls['line']}",
                "suggested_doc": f'"""TODO: Add description for {cls["name"]} class.\n\nAttributes:\n    TODO\n"""'
            })
        
        # Calculate documentation score
        total_items = doc_analysis["functions_found"] + doc_analysis["classes_found"]
        documented_items = total_items - doc_analysis["undocumented_items"]
        doc_score = (documented_items / max(total_items, 1)) * 100
        
        # Determine documentation quality
        if doc_analysis["documentation_ratio"] > 0.5:
            doc_quality = "good"
        elif doc_analysis["documentation_ratio"] > 0.2:
            doc_quality = "fair"
        else:
            doc_quality = "poor"
        
        return {
            "documentation_score": int(doc_score),
            "missing_docs": missing_docs,
            "suggested_readme_updates": [],
            "changelog_entry": self._generate_changelog_entry(diff),
            "inline_comments_needed": [],
            "existing_docs_quality": doc_quality,
            "summary": f"Found {doc_analysis['undocumented_items']} undocumented items. Documentation coverage: {doc_score:.0f}%"
        }
    
    def _generate_changelog_entry(self, diff: str) -> str:
        """Generate a simple changelog entry based on diff"""
        # Count additions and deletions
        additions = sum(1 for line in diff.split('\n') if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff.split('\n') if line.startswith('-') and not line.startswith('---'))
        
        if additions > deletions:
            return f"Added new functionality ({additions} lines added)"
        elif deletions > additions:
            return f"Refactored/removed code ({deletions} lines removed)"
        else:
            return f"Updated existing code ({additions} lines modified)"
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process and validate documentation analysis response"""
        try:
            # Try to parse JSON response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response
                
            result = json.loads(json_str)
            
            # Validate expected fields
            if "documentation_score" not in result:
                result["documentation_score"] = 50
            if "missing_docs" not in result:
                result["missing_docs"] = []
            if "suggested_readme_updates" not in result:
                result["suggested_readme_updates"] = []
            if "changelog_entry" not in result:
                result["changelog_entry"] = "Code changes made"
            if "inline_comments_needed" not in result:
                result["inline_comments_needed"] = []
            if "existing_docs_quality" not in result:
                result["existing_docs_quality"] = "fair"
                
            return result
            
        except json.JSONDecodeError:
            # Fallback to raw response
            return {
                "raw_response": response,
                "documentation_score": 0,
                "parsing_error": "Failed to parse JSON response"
            } 