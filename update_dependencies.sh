#!/bin/bash

echo "🔄 Updating Auto-Brainlift dependencies for Phase 2 (Smart Caching)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies updated successfully!"
echo ""
echo "To test the caching system, run:"
echo "  source venv/bin/activate"
echo "  python test_cache.py" 