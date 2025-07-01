const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🐍 Auto-Brainlift Python Bundler for Demo');
console.log('=========================================\n');

// For demo purposes, we'll create a simple Python wrapper
// that checks for dependencies and installs them if needed

const pythonWrapperScript = `#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from pathlib import Path

def check_and_install_dependencies():
    """Check if dependencies are installed, install if missing"""
    required_packages = [
        'langchain==0.3.16',
        'langchain-openai==0.3.27',
        'langchain-core==0.3.67',
        'langgraph==0.3.24',
        'gitpython==3.1.43',
        'openai==1.93.0',
        'python-dotenv==1.0.1',
        'pydantic==2.7.4',
        'typing-extensions==4.12.2',
        'numpy==1.26.4'
    ]
    
    missing_packages = []
    for package in required_packages:
        pkg_name = package.split('==')[0]
        try:
            __import__(pkg_name.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing missing packages: {missing_packages}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("Dependencies installed successfully!")
    
    return True

def main():
    """Main entry point for the wrapper"""
    # Set up paths
    script_dir = Path(__file__).parent
    agents_dir = script_dir / 'agents'
    
    # Add agents directory to Python path
    sys.path.insert(0, str(agents_dir))
    
    # Check dependencies
    try:
        check_and_install_dependencies()
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        print("Please ensure pip is installed and you have internet connection")
        sys.exit(1)
    
    # Import and run the actual agent
    try:
        from langgraph_agent import main as agent_main
        agent_main()
    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
`;

function createPythonWrapper() {
    console.log('📝 Creating Python wrapper script...');
    
    // Create the wrapper script
    fs.writeFileSync('python_wrapper.py', pythonWrapperScript);
    
    // Make it executable on Unix-like systems
    if (process.platform !== 'win32') {
        execSync('chmod +x python_wrapper.py');
    }
    
    console.log('✅ Python wrapper created successfully!');
}

function createBatchWrapper() {
    // For Windows users
    const batchScript = `@echo off
python "%~dp0python_wrapper.py" %*
`;
    
    fs.writeFileSync('run_agent.bat', batchScript);
    console.log('✅ Windows batch wrapper created!');
}

function createShellWrapper() {
    // For Mac/Linux users
    const shellScript = `#!/bin/bash
python3 "$(dirname "$0")/python_wrapper.py" "$@"
`;
    
    fs.writeFileSync('run_agent.sh', shellScript);
    execSync('chmod +x run_agent.sh');
    console.log('✅ Unix shell wrapper created!');
}

// Main execution
try {
    createPythonWrapper();
    
    if (process.platform === 'win32') {
        createBatchWrapper();
    } else {
        createShellWrapper();
    }
    
    console.log('\n🎉 Python bundling complete!');
    console.log('The app will now handle Python dependencies automatically.');
    
} catch (error) {
    console.error('❌ Error during Python bundling:', error);
    process.exit(1);
} 