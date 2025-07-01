#!/usr/bin/env python3
"""
Test script for the LangGraph agent
Run this to verify the agent is working correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Check if .env exists
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    print("❌ Error: .env file not found!")
    print("Please copy .env.template to .env and add your OpenAI API key")
    sys.exit(1)

# Load .env and check API key
from dotenv import load_dotenv
load_dotenv()

if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
    print("❌ Error: OPENAI_API_KEY not set in .env file!")
    print("Please add your OpenAI API key to the .env file")
    sys.exit(1)

print("✅ Environment configured correctly")
print("🧪 Testing LangGraph agent...")

try:
    from agents.langgraph_agent import GitCommitSummarizer
    
    # Create summarizer
    summarizer = GitCommitSummarizer()
    print("✅ Agent initialized successfully")
    
    # Test with dummy data
    test_state = {
        "commit_hash": "test123",
        "commit_message": "Test commit for Auto-Brainlift",
        "commit_author": "Test User <test@example.com>",
        "commit_date": "2025-06-30 10:00:00",
        "git_diff": """
diff --git a/test.py b/test.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/test.py
@@ -0,0 +1,5 @@
+def hello_world():
+    print("Hello from Auto-Brainlift!")
+
+if __name__ == "__main__":
+    hello_world()
"""
    }
    
    print("🔄 Running summarization workflow...")
    
    # Just test the individual functions without Git
    state = summarizer.summarize_context(test_state)
    print("✅ Context summary generated")
    
    state = summarizer.summarize_brainlift(state)
    print("✅ Brainlift summary generated")
    
    # Write outputs
    state = summarizer.write_output(state)
    print("✅ Output files written")
    
    print(f"\n📄 Context log: {state['output_files']['context']}")
    print(f"📄 Brainlift: {state['output_files']['brainlift']}")
    
    print("\n🎉 Test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 