"""
Unit tests for knowledge_loader module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.knowledge_loader import KnowledgeLoader


@pytest.fixture
def temp_knowledge_dir():
    """Create a temporary knowledge directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        knowledge_dir = Path(tmpdir) / "knowledge"
        knowledge_dir.mkdir()
        
        # Create test knowledge files
        (knowledge_dir / "transactions.md").write_text("""
# Transactions

## Key Concepts
- txn_cd: D = Debit, C = Credit
- amt: Amount in cents

## Business Rules
- Revenue = sum of Credit transactions
""")
        
        (knowledge_dir / "users.md").write_text("""
# Users

## Tables
- users: All user accounts
- user_preferences: User settings

## Key Fields
- status: A = Active, I = Inactive
""")
        
        (knowledge_dir / "_joins.md").write_text("""
# Join Recipes

## User Transactions
JOIN users u ON t.user_id = u.id
""")
        
        yield knowledge_dir


class TestKnowledgeLoader:
    """Tests for KnowledgeLoader class."""
    
    def test_exists(self, temp_knowledge_dir):
        """Test existence check."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        assert loader.exists()
        
        loader_nonexistent = KnowledgeLoader("/nonexistent/path")
        assert not loader_nonexistent.exists()
    
    def test_list_files(self, temp_knowledge_dir):
        """Test listing knowledge files."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        files = loader.list_files()
        
        assert len(files) == 3
        filenames = [f.name for f in files]
        assert 'transactions.md' in filenames
        assert 'users.md' in filenames
        assert '_joins.md' in filenames
    
    def test_load_file(self, temp_knowledge_dir):
        """Test loading a specific file."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        content = loader.load_file("transactions.md")
        
        assert content is not None
        assert 'Revenue' in content
        assert 'txn_cd' in content
    
    def test_load_nonexistent_file(self, temp_knowledge_dir):
        """Test loading a nonexistent file."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        content = loader.load_file("nonexistent.md")
        
        assert content is None
    
    def test_extract_keywords(self, temp_knowledge_dir):
        """Test keyword extraction."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        
        keywords = loader.extract_keywords("Show me the total revenue from transactions")
        
        assert 'revenue' in keywords
        assert 'transactions' in keywords
        # Stop words should be excluded
        assert 'the' not in keywords
        assert 'from' not in keywords
    
    def test_find_relevant_files(self, temp_knowledge_dir):
        """Test finding relevant files for a query."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        
        # Query about transactions - should match transactions.md by filename
        relevant = loader.find_relevant_files("Show all transactions")
        assert 'transactions.md' in relevant
        
        # Query about users - should match users.md by filename
        relevant = loader.find_relevant_files("Show user accounts")
        assert 'users.md' in relevant
    
    def test_always_include_joins(self, temp_knowledge_dir):
        """Test that _joins.md is always included."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        
        relevant = loader.find_relevant_files("Any query")
        assert '_joins.md' in relevant
    
    def test_get_context(self, temp_knowledge_dir):
        """Test getting combined context."""
        loader = KnowledgeLoader(temp_knowledge_dir)
        
        context = loader.get_context("Show revenue from transactions")
        
        assert 'DOMAIN KNOWLEDGE' in context
        assert 'transactions.md' in context
        assert 'Revenue' in context
    
    def test_empty_knowledge_dir(self):
        """Test handling empty knowledge directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty_knowledge"
            empty_dir.mkdir()
            
            loader = KnowledgeLoader(empty_dir)
            context = loader.get_context("Any query")
            
            assert context == ""
