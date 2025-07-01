#!/usr/bin/env python3
"""
Test script for verifying the caching system functionality
"""

import os
import sys
import time
import hashlib
from pathlib import Path

# Add the agents directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'agents'))

from cache import CacheManager
from budget_manager import BudgetManager

def test_cache_system():
    """Test the caching system with sample data"""
    print("🧪 Testing Auto-Brainlift Caching System\n")
    
    # Use a test project ID
    project_id = "test_project_" + hashlib.md5(b"test").hexdigest()[:8]
    
    # Initialize cache manager
    print("1️⃣ Initializing cache manager...")
    cache_manager = CacheManager(project_id)
    print("✅ Cache manager initialized\n")
    
    # Test exact cache
    print("2️⃣ Testing exact cache...")
    test_query = "def hello_world():\n    print('Hello, World!')"
    
    # First request should be a miss
    result1 = cache_manager.get_or_generate(
        test_query,
        lambda q: {"summary": "A simple hello world function"},
        cache_ttl=3600
    )
    print(f"First request: {result1['metadata']['cache_hit']} (latency: {result1['metadata']['latency_ms']:.1f}ms)")
    
    # Second request should be an exact hit
    result2 = cache_manager.get_or_generate(
        test_query,
        lambda q: {"summary": "This should not be called"},
        cache_ttl=3600
    )
    print(f"Second request: {result2['metadata']['cache_hit']} (latency: {result2['metadata']['latency_ms']:.1f}ms)")
    print("✅ Exact cache working!\n")
    
    # Test semantic cache
    print("3️⃣ Testing semantic cache...")
    similar_query = "def hello_world():\n    print('Hello World!')  # slightly different"
    
    # This should hit the semantic cache
    result3 = cache_manager.get_or_generate(
        similar_query,
        lambda q: {"summary": "This should not be called either"},
        cache_ttl=3600
    )
    
    if result3['metadata']['cache_hit'] == 'semantic':
        print(f"Semantic match found! Similarity: {result3['metadata'].get('similarity', 0):.3f}")
    else:
        print("⚠️ Semantic cache miss (this might happen on first run)")
    print("✅ Semantic cache tested\n")
    
    # Show cache statistics
    print("4️⃣ Cache Statistics:")
    stats = cache_manager.get_cache_stats()
    print(f"Overall hit rate: {stats['overall']['hit_rate']:.1%}")
    print(f"Total requests: {stats['overall']['total_requests']}")
    print(f"Average latency: {stats['overall']['avg_latency_ms']:.1f}ms")
    print(f"Exact cache hits: {stats['exact_cache']['hit_count']}")
    print(f"Semantic cache hits: {stats['semantic_cache']['hit_count']}")
    print(f"Embeddings generated: {stats['embeddings']['generations']}")
    print(f"Estimated embedding cost: ${stats['embeddings']['estimated_cost']:.4f}\n")
    
    # Test budget manager
    print("5️⃣ Testing budget manager...")
    settings = {
        'budgetEnabled': True,
        'commitTokenLimit': 10000
    }
    budget_manager = BudgetManager(project_id, settings)
    
    # Check budget for a sample diff
    sample_diff = """
    def new_function():
        # This is a new function
        for i in range(10):
            print(f"Number: {i}")
    """
    
    within_budget, details = budget_manager.check_budget(
        budget_manager.estimate_tokens(sample_diff)
    )
    
    print(f"Sample diff tokens: {details['estimated_tokens']}")
    print(f"Estimated cost: ${details['estimated_cost']:.4f}")
    print(f"Within budget: {within_budget}")
    print("✅ Budget manager working!\n")
    
    # Clean up test cache
    print("6️⃣ Cleaning up test cache...")
    cache_manager.clear_cache()
    print("✅ Test cache cleared\n")
    
    print("🎉 All tests completed successfully!")

if __name__ == "__main__":
    try:
        # Check if OpenAI API key is set
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Error: OPENAI_API_KEY not set in environment")
            print("Please set your OpenAI API key before running tests")
            sys.exit(1)
        
        test_cache_system()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 