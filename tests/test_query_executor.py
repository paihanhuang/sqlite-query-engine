"""
Unit tests for query_executor module.
"""

import os
import sqlite3
import tempfile

import pytest

from src.query_executor import QueryExecutor, QueryResult


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        );
        
        INSERT INTO users VALUES (1, 'Alice', 'alice@example.com');
        INSERT INTO users VALUES (2, 'Bob', 'bob@example.com');
    """)
    conn.close()
    
    yield path
    
    os.unlink(path)


class TestQueryExecutor:
    """Tests for QueryExecutor class."""
    
    def test_execute_select(self, temp_db):
        """Test executing a simple SELECT query."""
        executor = QueryExecutor(temp_db)
        result = executor.execute("SELECT * FROM users")
        
        assert result.success
        assert result.row_count == 2
        assert 'id' in result.columns
        assert 'name' in result.columns
    
    def test_block_insert_in_readonly(self, temp_db):
        """Test that INSERT is blocked in read-only mode."""
        executor = QueryExecutor(temp_db, read_only=True)
        result = executor.execute("INSERT INTO users VALUES (3, 'Carol', 'carol@test.com')")
        
        assert not result.success
        assert 'blocked' in result.error.lower()
    
    def test_block_delete_in_readonly(self, temp_db):
        """Test that DELETE is blocked in read-only mode."""
        executor = QueryExecutor(temp_db, read_only=True)
        result = executor.execute("DELETE FROM users WHERE id = 1")
        
        assert not result.success
        assert 'blocked' in result.error.lower()
    
    def test_block_update_in_readonly(self, temp_db):
        """Test that UPDATE is blocked in read-only mode."""
        executor = QueryExecutor(temp_db, read_only=True)
        result = executor.execute("UPDATE users SET name = 'Test' WHERE id = 1")
        
        assert not result.success
        assert 'blocked' in result.error.lower()
    
    def test_block_drop_in_readonly(self, temp_db):
        """Test that DROP is blocked in read-only mode."""
        executor = QueryExecutor(temp_db, read_only=True)
        result = executor.execute("DROP TABLE users")
        
        assert not result.success
        assert 'blocked' in result.error.lower()
    
    def test_block_multiple_statements(self, temp_db):
        """Test that multiple statements are blocked."""
        executor = QueryExecutor(temp_db)
        result = executor.execute("SELECT 1; SELECT 2")
        
        assert not result.success
        assert 'multiple' in result.error.lower()
    
    def test_auto_add_limit(self, temp_db):
        """Test that LIMIT is automatically added."""
        executor = QueryExecutor(temp_db, max_results=10)
        result = executor.execute("SELECT * FROM users")
        
        assert result.success
        assert 'LIMIT' in result.sql.upper()
    
    def test_respect_existing_limit(self, temp_db):
        """Test that existing LIMIT is respected."""
        executor = QueryExecutor(temp_db)
        result = executor.execute("SELECT * FROM users LIMIT 1")
        
        assert result.success
        assert result.row_count == 1
    
    def test_handle_sql_error(self, temp_db):
        """Test handling of SQL errors."""
        executor = QueryExecutor(temp_db)
        result = executor.execute("SELECT * FROM nonexistent_table")
        
        assert not result.success
        assert result.error is not None
    
    def test_is_safe_query(self, temp_db):
        """Test safety check for queries."""
        executor = QueryExecutor(temp_db)
        
        safe, _ = executor.is_safe_query("SELECT * FROM users")
        assert safe
        
        safe, _ = executor.is_safe_query("INSERT INTO users VALUES (1, 'a', 'b')")
        assert not safe
