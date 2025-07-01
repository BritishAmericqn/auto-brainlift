#!/usr/bin/env python3
"""
Test script to verify that the git hook automation is working correctly
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def check_git_hook():
    """Check if the git hook is installed"""
    hook_path = Path(".git/hooks/post-commit")
    if not hook_path.exists():
        print("❌ Git hook not installed! Run ./setup_git_hook.sh first")
        return False
    
    print("✅ Git hook is installed")
    
    # Check if it's executable
    if not os.access(hook_path, os.X_OK):
        print("❌ Git hook is not executable!")
        return False
    
    print("✅ Git hook is executable")
    return True

def check_python_env():
    """Check if Python environment is set up"""
    venv_path = Path("venv/bin/python")
    if venv_path.exists():
        print("✅ Virtual environment found")
        return True
    else:
        print("⚠️  Virtual environment not found, will use system Python")
        return True

def check_directories():
    """Check if output directories exist or can be created"""
    dirs = ["brainlifts", "context_logs", "error_logs", "logs"]
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"✅ Created directory: {dir_name}/")
            except Exception as e:
                print(f"❌ Failed to create directory {dir_name}/: {e}")
                return False
        else:
            print(f"✅ Directory exists: {dir_name}/")
    return True

def test_git_hook_handler():
    """Test the git hook handler directly"""
    print("\n🧪 Testing git_hook_handler.py directly...")
    
    # Get Python command
    venv_python = Path("venv/bin/python")
    python_cmd = str(venv_python) if venv_python.exists() else "python3"
    
    # Run the git hook handler
    try:
        result = subprocess.run(
            [python_cmd, "agents/git_hook_handler.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Git hook handler executed successfully")
            print("📋 Output:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
            
            # Check if log was created
            log_path = Path("logs/git_hook.log")
            if log_path.exists():
                print("✅ Git hook log created")
                # Read last few lines
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print("📝 Last log entry:", lines[-1].strip())
            
            return True
        else:
            print("❌ Git hook handler failed")
            print("Error:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Git hook handler timed out")
        return False
    except Exception as e:
        print(f"❌ Error running git hook handler: {e}")
        return False

def check_latest_commit():
    """Check the latest commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            print(f"📍 Latest commit: {commit_hash[:8]}")
            return commit_hash
        else:
            print("❌ Failed to get latest commit")
            return None
    except Exception as e:
        print(f"❌ Error getting commit hash: {e}")
        return None

def check_generated_files():
    """Check if files were generated"""
    print("\n📂 Checking for generated files...")
    
    found_files = False
    
    # Check brainlifts
    brainlifts_dir = Path("brainlifts")
    if brainlifts_dir.exists():
        md_files = list(brainlifts_dir.glob("*.md"))
        if md_files:
            print(f"✅ Found {len(md_files)} brainlift file(s)")
            latest = max(md_files, key=lambda p: p.stat().st_mtime)
            print(f"   Latest: {latest.name}")
            found_files = True
        else:
            print("⚠️  No brainlift files found yet")
    
    # Check context logs
    context_dir = Path("context_logs")
    if context_dir.exists():
        md_files = list(context_dir.glob("*.md"))
        if md_files:
            print(f"✅ Found {len(md_files)} context log file(s)")
            latest = max(md_files, key=lambda p: p.stat().st_mtime)
            print(f"   Latest: {latest.name}")
            found_files = True
        else:
            print("⚠️  No context log files found yet")
    
    return found_files

def main():
    """Run all checks"""
    print("🧠 Auto-Brainlift Automation Test")
    print("=================================\n")
    
    # Check git repository
    if not Path(".git").exists():
        print("❌ Not in a Git repository!")
        print("   Please run this from your project root")
        return 1
    
    print("✅ Git repository detected")
    
    # Run checks
    checks = [
        ("Git Hook", check_git_hook),
        ("Python Environment", check_python_env),
        ("Output Directories", check_directories),
        ("Latest Commit", check_latest_commit),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        if not check_func():
            all_passed = False
    
    # Test the git hook handler
    if all_passed:
        test_git_hook_handler()
        check_generated_files()
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ All checks passed! Auto-Brainlift automation is ready.")
        print("\nNext steps:")
        print("1. Make a commit: git commit -m 'Test commit'")
        print("2. Check logs/git_hook.log for processing details")
        print("3. Look for new files in brainlifts/ and context_logs/")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 