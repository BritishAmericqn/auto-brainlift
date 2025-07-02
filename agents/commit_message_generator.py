#!/usr/bin/env python3
"""
Commit Message Generator
Generates AI-powered commit messages from git diff using OpenAI
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def generate_commit_message():
    """Generate commit message from git diff"""
    
    git_diff = os.getenv('GIT_DIFF', '')
    if not git_diff:
        print("Error: No git diff provided")
        sys.exit(1)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OpenAI API key not provided")
        sys.exit(1)
    
    try:
        # Initialize LLM - using cost-effective model for commit messages
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=api_key
        )
        
        # Create messages
        system_msg = SystemMessage(content="""
You are an expert developer writing git commit messages.
Generate a concise, descriptive commit message based on the git diff.
Follow conventional commit format: type(scope): description

Examples:
- feat: add user authentication system
- fix: resolve memory leak in cache manager
- docs: update API documentation
- style: fix code formatting issues
- refactor: simplify database connection logic
- test: add unit tests for payment module
- chore: update dependencies

Rules:
1. Keep it under 50 characters for the main message
2. Be specific about what changed
3. Use imperative mood (add, fix, update, not added, fixed, updated)
4. Don't mention file names unless critical to understanding
5. Focus on the "what" and "why", not the "how"
6. Use appropriate type: feat, fix, docs, style, refactor, test, chore
7. Add scope in parentheses if it helps clarify (e.g., "fix(auth): resolve login bug")
""")
        
        human_msg = HumanMessage(content=f"Generate a commit message for this git diff:\n\n{git_diff}")
        
        # Generate message
        response = llm.invoke([system_msg, human_msg])
        commit_message = response.content.strip()
        
        # Clean up the message (remove quotes if present)
        if commit_message.startswith('"') and commit_message.endswith('"'):
            commit_message = commit_message[1:-1]
        if commit_message.startswith("'") and commit_message.endswith("'"):
            commit_message = commit_message[1:-1]
        
        # Ensure it's not too long
        if len(commit_message) > 72:
            # If too long, try to shorten by removing scope or details
            parts = commit_message.split(':')
            if len(parts) >= 2:
                type_part = parts[0]
                desc_part = ':'.join(parts[1:]).strip()
                if len(desc_part) > 50:
                    desc_part = desc_part[:47] + '...'
                commit_message = f"{type_part}: {desc_part}"
        
        print(commit_message)
        
    except Exception as e:
        print(f"Error generating commit message: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_commit_message() 