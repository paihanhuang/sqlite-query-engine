"""
Unit tests for schema_extractor module.
"""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.schema_extractor import SchemaExtractor, Schema, Table, Column, ForeignKey


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            budget REAL
        );
        
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            department_id INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );
        
        INSERT INTO departments VALUES (1, 'Engineering', 500000);
        INSERT INTO users VALUES (1, 'Alice', 'alice@example.com', 1);
    """)
    conn.close()
    
    yield path
    
    os.unlink(path)


class TestSchemaExtractor:
    """Tests for SchemaExtractor class."""
    
    def test_extract_tables(self, temp_db):
        """Test that tables are extracted correctly."""
        extractor = SchemaExtractor(temp_db)
        schema = extractor.extract()
        
        assert len(schema.tables) == 2
        table_names = [t.name for t in schema.tables]
        assert 'departments' in table_names
        assert 'users' in table_names
    
    def test_extract_columns(self, temp_db):
        """Test that columns are extracted correctly."""
        extractor = SchemaExtractor(temp_db)
        schema = extractor.extract()
        
        users_table = next(t for t in schema.tables if t.name == 'users')
        column_names = [c.name for c in users_table.columns]
        
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'email' in column_names
        assert 'department_id' in column_names
    
    def test_extract_primary_keys(self, temp_db):
        """Test that primary keys are identified."""
        extractor = SchemaExtractor(temp_db)
        schema = extractor.extract()
        
        users_table = next(t for t in schema.tables if t.name == 'users')
        pk_columns = [c for c in users_table.columns if c.is_primary_key]
        
        assert len(pk_columns) == 1
        assert pk_columns[0].name == 'id'
    
    def test_extract_foreign_keys(self, temp_db):
        """Test that foreign keys are extracted."""
        extractor = SchemaExtractor(temp_db)
        schema = extractor.extract()
        
        assert len(schema.foreign_keys) == 1
        fk = schema.foreign_keys[0]
        assert fk.from_table == 'users'
        assert fk.from_column == 'department_id'
        assert fk.to_table == 'departments'
        assert fk.to_column == 'id'
    
    def test_to_prompt_string(self, temp_db):
        """Test schema conversion to prompt string."""
        extractor = SchemaExtractor(temp_db)
        schema = extractor.extract()
        
        prompt = schema.to_prompt_string()
        
        assert 'DATABASE SCHEMA' in prompt
        assert 'departments' in prompt
        assert 'users' in prompt
        assert 'RELATIONSHIPS' in prompt
    
    def test_nonexistent_database(self):
        """Test that FileNotFoundError is raised for missing db."""
        with pytest.raises(FileNotFoundError):
            SchemaExtractor('/nonexistent/path.db')
    
    def test_get_sample_data(self, temp_db):
        """Test getting sample data from table."""
        extractor = SchemaExtractor(temp_db)
        samples = extractor.get_sample_data('users', limit=3)
        
        assert len(samples) == 1
        assert samples[0]['name'] == 'Alice'
