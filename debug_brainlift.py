#!/usr/bin/env python3
"""Simple debug script for Auto-Brainlift issues (no langchain dependencies)"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

def check_environment():
    """Check environment setup"""
    print("\n" + "="*60)
    print("ENVIRONMENT CHECK")
    print("="*60)
    
    # Check environment variables
    env_vars = [
        'CURSOR_CHAT_ENABLED',
        'CURSOR_CHAT_PATH', 
        'CURSOR_CHAT_MODE',
        'CURSOR_CHAT_INCLUDE_IN_SUMMARY',
        'OPENAI_API_KEY'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'OPENAI_API_KEY' and value != 'NOT SET':
            value = value[:10] + '...'  # Hide API key
        print(f"{var}: {value}")

def test_cursor_chat_direct():
    """Test Cursor chat database directly"""
    print("\n" + "="*60)
    print("TESTING CURSOR CHAT DATABASE")
    print("="*60)
    
    # Check database path
    db_path = Path.home() / 'Library' / 'Application Support' / 'Cursor' / 'User' / 'globalStorage' / 'state.vscdb'
    print(f"Database path: {db_path}")
    print(f"Database exists: {db_path.exists()}")
    
    if not db_path.exists():
        print("\nERROR: Database not found!")
        return
        
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\nTables found: {[t[0] for t in tables]}")
        
        # Count bubble entries
        cursor.execute("SELECT COUNT(*) FROM cursorDiskKV WHERE key LIKE 'bubbleId:%'")
        count = cursor.fetchone()[0]
        print(f"\nTotal bubble (chat) entries: {count}")
        
        # Get sample bubbles
        cursor.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'bubbleId:%' LIMIT 5")
        bubbles = cursor.fetchall()
        
        print(f"\nSample chat entries:")
        valid_chats = 0
        for i, (key, value) in enumerate(bubbles):
            try:
                # Parse JSON
                if isinstance(value, bytes):
                    data = json.loads(value.decode('utf-8'))
                else:
                    data = json.loads(value)
                
                text = data.get('text', '')
                msg_type = data.get('type', 0)
                
                if text and text != '...':
                    valid_chats += 1
                    print(f"\n  Chat {i+1}:")
                    print(f"    Type: {'user' if msg_type == 1 else 'assistant'}")
                    print(f"    Text preview: {text[:100]}...")
                    
            except Exception as e:
                print(f"    Error parsing bubble: {e}")
        
        print(f"\nValid chat messages found in sample: {valid_chats}")
        
        conn.close()
        
    except Exception as e:
        print(f"\nERROR accessing database: {e}")

def check_cache_directory():
    """Check cache directory structure"""
    print("\n" + "="*60)
    print("CHECKING CACHE DIRECTORY")
    print("="*60)
    
    # Check cache directory
    cache_dir = Path.home() / 'Library' / 'Application Support' / 'auto-brainlift' / 'cache'
    print(f"Cache directory: {cache_dir}")
    print(f"Cache directory exists: {cache_dir.exists()}")
    
    if cache_dir.exists():
        # List subdirectories
        subdirs = [d for d in cache_dir.iterdir() if d.is_dir()]
        print(f"\nCache subdirectories: {[d.name for d in subdirs]}")
        
        # Check exact cache
        exact_dir = cache_dir / 'exact'
        if exact_dir.exists():
            files = list(exact_dir.glob('*'))
            print(f"\nExact cache entries: {len(files)}")
            
            # Show recent entries
            if files:
                print("\nRecent cache entries:")
                for f in sorted(files)[-5:]:
                    stat = f.stat()
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    print(f"  - {f.name} (modified: {mod_time})")
                    
                    # Try to read one entry
                    if f.name.endswith('.json'):
                        try:
                            with open(f, 'r') as file:
                                data = json.load(file)
                                print(f"    Keys: {list(data.keys())[:5]}")
                        except:
                            pass
    else:
        print("\nCache directory doesn't exist - this might be why caching isn't working!")

def check_git_info():
    """Check git repository info"""
    print("\n" + "="*60)
    print("CHECKING GIT INFO")
    print("="*60)
    
    # Check if we're in a git repo
    git_dir = Path('.git')
    print(f"In git repository: {git_dir.exists()}")
    
    if git_dir.exists():
        # Try to get current commit hash
        try:
            head_file = git_dir / 'HEAD'
            if head_file.exists():
                with open(head_file, 'r') as f:
                    ref = f.read().strip()
                    print(f"HEAD: {ref}")
                    
                    if ref.startswith('ref: '):
                        ref_path = git_dir / ref[5:]
                        if ref_path.exists():
                            with open(ref_path, 'r') as f:
                                commit_hash = f.read().strip()
                                print(f"Current commit: {commit_hash[:8]}")
        except Exception as e:
            print(f"Error reading git info: {e}")

if __name__ == "__main__":
    print("Auto-Brainlift Simple Debug Script")
    print("==================================")
    
    check_environment()
    test_cursor_chat_direct()
    check_cache_directory()
    check_git_info()
    
    print("\n\nDebug complete!")
    print("\nNOTE: If you're seeing import errors, you may need to install dependencies:")
    print("  pip install -r requirements.txt") 