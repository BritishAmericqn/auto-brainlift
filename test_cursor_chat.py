#!/usr/bin/env python3
"""
Tests for Cursor Chat Reading functionality
TO BE REMOVED after feature validation
"""

import os
import sqlite3
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.cursor_chat_reader import CursorChatReader


class TestCursorChatReader:
    """Test suite for CursorChatReader - REMOVE AFTER VALIDATION"""
    
    @pytest.fixture
    def mock_cursor_db(self):
        """Create a mock Cursor SQLite database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create mock database structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a simplified version of Cursor's schema
        cursor.execute('''
            CREATE TABLE aiService_prompts (
                id INTEGER PRIMARY KEY,
                timestamp INTEGER,
                project_path TEXT,
                prompt TEXT,
                response TEXT,
                metadata TEXT
            )
        ''')
        
        # Insert test data
        base_time = int(datetime.now().timestamp() * 1000)
        test_data = [
            # Old chat (should be filtered out)
            (base_time - 7200000, "/test/project", "How do I implement feature X?", 
             "To implement feature X, you should...", '{"model": "gpt-4"}'),
            # Recent chat (should be included)
            (base_time - 1800000, "/test/project", "Fix the authentication bug", 
             "The authentication bug can be fixed by...", '{"model": "gpt-4"}'),
            # Very recent chat
            (base_time - 300000, "/test/project", "Add error handling", 
             "For proper error handling, consider...", '{"model": "gpt-4"}'),
        ]
        
        cursor.executemany(
            'INSERT INTO aiService_prompts (timestamp, project_path, prompt, response, metadata) VALUES (?, ?, ?, ?, ?)',
            test_data
        )
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    def test_read_chats_after_timestamp(self, mock_cursor_db):
        """Test reading chats after a specific timestamp"""
        reader = CursorChatReader(mock_cursor_db)
        
        # Read chats from last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        chats = reader.read_chats_after_timestamp(one_hour_ago)
        
        assert len(chats) == 2  # Should get 2 recent chats
        assert "Fix the authentication bug" in chats[0]['prompt']
        assert "Add error handling" in chats[1]['prompt']
    
    def test_filter_by_project_path(self, mock_cursor_db):
        """Test filtering chats by project path"""
        reader = CursorChatReader(mock_cursor_db)
        
        chats = reader.read_chats_after_timestamp(
            datetime.now() - timedelta(hours=3),
            project_path="/test/project"
        )
        
        assert all(chat['project_path'] == "/test/project" for chat in chats)
    
    def test_parse_chat_content(self, mock_cursor_db):
        """Test parsing and cleaning chat content"""
        reader = CursorChatReader(mock_cursor_db)
        
        chats = reader.read_chats_after_timestamp(datetime.now() - timedelta(hours=1))
        parsed = reader.parse_chat_content(chats)
        
        assert 'prompts' in parsed
        assert 'responses' in parsed
        assert 'combined' in parsed
        assert len(parsed['prompts']) == 2
        assert len(parsed['responses']) == 2
    
    def test_missing_database(self):
        """Test handling of missing database file"""
        reader = CursorChatReader("/nonexistent/path.db")
        chats = reader.read_chats_after_timestamp(datetime.now())
        
        assert chats == []  # Should return empty list, not crash
    
    def test_extract_development_insights(self, mock_cursor_db):
        """Test extracting key development insights from chats"""
        reader = CursorChatReader(mock_cursor_db)
        
        chats = reader.read_chats_after_timestamp(datetime.now() - timedelta(hours=1))
        insights = reader.extract_development_insights(chats)
        
        assert 'key_decisions' in insights
        assert 'implementation_notes' in insights
        assert 'bug_fixes' in insights


if __name__ == "__main__":
    # Run tests
    print("Running Cursor Chat Reader tests...")
    print("=" * 50)
    
    # Create test instance
    test_instance = TestCursorChatReader()
    
    # Run each test
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Setup mock database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE aiService_prompts (
                id INTEGER PRIMARY KEY,
                timestamp INTEGER,
                project_path TEXT,
                prompt TEXT,
                response TEXT,
                metadata TEXT
            )
        ''')
        
        base_time = int(datetime.now().timestamp() * 1000)
        cursor.executemany(
            'INSERT INTO aiService_prompts (timestamp, project_path, prompt, response, metadata) VALUES (?, ?, ?, ?, ?)',
            [
                (base_time - 7200000, "/test/project", "How do I implement feature X?", 
                 "To implement feature X, you should...", '{"model": "gpt-4"}'),
                (base_time - 1800000, "/test/project", "Fix the authentication bug", 
                 "The authentication bug can be fixed by...", '{"model": "gpt-4"}'),
                (base_time - 300000, "/test/project", "Add error handling", 
                 "For proper error handling, consider...", '{"model": "gpt-4"}'),
            ]
        )
        conn.commit()
        conn.close()
        
        # Mock reader for testing
        print("\n✓ Created mock Cursor database")
        
        # Test placeholder
        print("✓ Test framework ready")
        print("\nNote: Full tests will run when CursorChatReader is implemented")
        
    finally:
        os.unlink(db_path)
    
    print("\n" + "=" * 50)
    print("Test setup complete!") 