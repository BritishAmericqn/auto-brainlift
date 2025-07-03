#!/usr/bin/env python3
"""
Test script for Cursor Chat Agent integration
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.cursor_chat_agent import CursorChatAgent
from agents.agent_orchestrator import AgentOrchestrator
from agents.base_agent import AgentState

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_cursor_chat_agent():
    """Test the cursor chat agent standalone"""
    print("\n" + "="*60)
    print("Testing Cursor Chat Agent")
    print("="*60)
    
    # Initialize agent
    agent = CursorChatAgent(enabled=True, model="gpt-4-turbo")
    print(f"✓ Initialized: {agent}")
    
    # Create test state
    state = AgentState({
        "git_diff": "Sample git diff for testing",
        "commit_info": {
            "commit_hash": "abc123",
            "commit_message": "Test commit",
            "commit_author": "Test Author",
            "commit_date": datetime.now().isoformat()
        },
        "project_id": "test_project"
    })
    
    # Test analysis
    print("\nRunning analysis...")
    result_state = agent.analyze(state)
    
    # Check results
    if f"agent_{agent.name}" in result_state:
        agent_data = result_state[f"agent_{agent.name}"]
        print(f"\n✓ Agent completed analysis")
        
        if "error" in agent_data:
            print(f"⚠️  Error occurred: {agent_data['error']}")
        else:
            print(f"✓ Analysis successful")
            
            if "analysis" in agent_data:
                analysis = agent_data["analysis"]
                print(f"\nAnalysis Results:")
                print(f"  - Context Score: {analysis.get('context_score', 'N/A')}/100")
                print(f"  - Key Decisions: {len(analysis.get('key_decisions', []))}")
                print(f"  - Problems Solved: {len(analysis.get('problems_solved', []))}")
                print(f"  - Chat Count: {agent_data.get('chat_count', 0)}")
                print(f"  - Summary: {analysis.get('summary', 'N/A')}")
    else:
        print("✗ No agent results found in state")


def test_orchestrator_with_cursor_chat():
    """Test the orchestrator with cursor chat agent enabled"""
    print("\n" + "="*60)
    print("Testing Orchestrator with Cursor Chat Agent")
    print("="*60)
    
    # Set environment variables to enable cursor chat
    os.environ['CURSOR_CHAT_AGENT_ENABLED'] = 'true'
    os.environ['CURSOR_CHAT_AGENT_MODEL'] = 'gpt-4-turbo'
    os.environ['CURSOR_CHAT_ENABLED'] = 'true'
    os.environ['CURSOR_CHAT_MODE'] = 'light'
    
    # Initialize orchestrator
    settings = {
        'execution_mode': 'parallel',
        'agents': {
            'cursor_chat': {
                'enabled': True,
                'model': 'gpt-4-turbo'
            },
            'security': {
                'enabled': False,  # Disable others for this test
                'model': 'gpt-4-turbo'
            },
            'quality': {
                'enabled': False,
                'model': 'gpt-4-turbo'
            },
            'documentation': {
                'enabled': False,
                'model': 'gpt-4-turbo'
            }
        }
    }
    
    orchestrator = AgentOrchestrator("test_project", settings)
    print(f"✓ Initialized orchestrator with {len(orchestrator.agents)} agents")
    
    # Check cursor chat agent is enabled
    cursor_chat_agent = orchestrator.agents.get('cursor_chat')
    if cursor_chat_agent:
        print(f"✓ Cursor Chat Agent found: {cursor_chat_agent}")
        print(f"  - Enabled: {cursor_chat_agent.enabled}")
        print(f"  - Model: {cursor_chat_agent.model}")
    else:
        print("✗ Cursor Chat Agent not found in orchestrator")
        
    # Run analysis
    print("\nRunning orchestrated analysis...")
    result = orchestrator.analyze_commit(
        "Sample git diff",
        {
            "commit_hash": "test123",
            "commit_message": "Test commit",
            "commit_author": "Test Author",
            "commit_date": datetime.now().isoformat()
        }
    )
    
    # Check results
    print("\nOrchestrator Results:")
    print(f"  - Summary: {result.get('summary', 'N/A')}")
    print(f"  - Agents Run: {result.get('metrics', {}).get('agents_run', 0)}")
    print(f"  - Total Tokens: {result.get('metrics', {}).get('total_tokens', 0)}")
    
    if 'cursor_chat' in result.get('agents', {}):
        cursor_results = result['agents']['cursor_chat']
        print(f"\n✓ Cursor Chat Agent Results:")
        print(f"  - Status: {'Success' if 'error' not in cursor_results else 'Error'}")
        if 'analysis' in cursor_results:
            print(f"  - Context Score: {cursor_results['analysis'].get('context_score', 'N/A')}/100")


def test_integration_workflow():
    """Test the complete integration workflow"""
    print("\n" + "="*60)
    print("Testing Complete Integration Workflow")
    print("="*60)
    
    # This simulates what happens in the LangGraph workflow
    from agents.langgraph_agent import GitCommitSummarizer
    
    # Set up environment
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'test-key')
    os.environ['CURSOR_CHAT_AGENT_ENABLED'] = 'true'
    
    # Note: In a real test, you'd need a valid OpenAI API key
    print("\n⚠️  Note: Full workflow test requires valid OpenAI API key")
    print("   Set OPENAI_API_KEY environment variable to test with real API")
    
    if os.getenv('OPENAI_API_KEY', '').startswith('sk-'):
        print("\n✓ OpenAI API key found, running full test...")
        
        try:
            summarizer = GitCommitSummarizer()
            print("✓ GitCommitSummarizer initialized")
            
            # Check if cursor chat agent is in the orchestrator
            if summarizer.agent_orchestrator:
                agents = summarizer.agent_orchestrator.agents
                if 'cursor_chat' in agents:
                    print(f"✓ Cursor Chat Agent integrated: {agents['cursor_chat']}")
                else:
                    print("✗ Cursor Chat Agent not found in workflow")
            else:
                print("✗ Agent orchestrator not initialized")
                
        except Exception as e:
            print(f"✗ Error initializing workflow: {e}")
    else:
        print("\n⚠️  Skipping full workflow test (no API key)")


if __name__ == "__main__":
    print("Testing Cursor Chat Agent Integration")
    print("=====================================")
    
    # Test 1: Standalone agent
    test_cursor_chat_agent()
    
    # Test 2: Orchestrator integration
    test_orchestrator_with_cursor_chat()
    
    # Test 3: Full workflow (requires API key)
    test_integration_workflow()
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60) 