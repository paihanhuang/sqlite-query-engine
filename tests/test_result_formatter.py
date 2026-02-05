"""
Unit tests for result_formatter module.
"""

import json

import pytest

from src.query_executor import QueryResult
from src.result_formatter import ResultFormatter


@pytest.fixture
def sample_result():
    """Create a sample query result."""
    return QueryResult(
        success=True,
        columns=["id", "name", "email"],
        rows=[
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
        ],
        row_count=2
    )


@pytest.fixture
def empty_result():
    """Create an empty query result."""
    return QueryResult(
        success=True,
        columns=["id", "name"],
        rows=[],
        row_count=0
    )


@pytest.fixture
def error_result():
    """Create an error query result."""
    return QueryResult(
        success=False,
        columns=[],
        rows=[],
        row_count=0,
        error="Table not found"
    )


class TestResultFormatter:
    """Tests for ResultFormatter class."""
    
    def test_to_csv(self, sample_result):
        """Test CSV output."""
        formatter = ResultFormatter()
        csv_output = formatter.to_csv(sample_result)
        
        lines = csv_output.strip().split('\n')
        assert len(lines) == 3  # header + 2 rows
        assert 'id,name,email' in lines[0]
        assert 'Alice' in lines[1]
        assert 'Bob' in lines[2]
    
    def test_to_json(self, sample_result):
        """Test JSON output."""
        formatter = ResultFormatter()
        json_output = formatter.to_json(sample_result)
        
        data = json.loads(json_output)
        assert len(data) == 2
        assert data[0]['name'] == 'Alice'
        assert data[1]['name'] == 'Bob'
    
    def test_to_markdown(self, sample_result):
        """Test Markdown output."""
        formatter = ResultFormatter()
        md_output = formatter.to_markdown(sample_result)
        
        assert '| id | name | email |' in md_output
        assert '| --- |' in md_output
        assert '| Alice |' in md_output or 'Alice' in md_output
    
    def test_empty_result_csv(self, empty_result):
        """Test CSV output for empty result."""
        formatter = ResultFormatter()
        csv_output = formatter.to_csv(empty_result)
        
        lines = csv_output.strip().split('\n')
        assert len(lines) == 1  # header only
    
    def test_empty_result_markdown(self, empty_result):
        """Test Markdown output for empty result."""
        formatter = ResultFormatter()
        md_output = formatter.to_markdown(empty_result)
        
        assert 'No results' in md_output
    
    def test_error_result_csv(self, error_result):
        """Test CSV output for error result."""
        formatter = ResultFormatter()
        output = formatter.to_csv(error_result)
        
        assert 'Error' in output
        assert 'Table not found' in output
    
    def test_error_result_json(self, error_result):
        """Test JSON output for error result."""
        formatter = ResultFormatter()
        json_output = formatter.to_json(error_result)
        
        data = json.loads(json_output)
        assert 'error' in data
        assert data['error'] == 'Table not found'
    
    def test_null_handling(self):
        """Test handling of NULL values."""
        result = QueryResult(
            success=True,
            columns=["id", "name"],
            rows=[(1, None), (2, "Bob")],
            row_count=2
        )
        
        formatter = ResultFormatter()
        
        # CSV should handle None
        csv_output = formatter.to_csv(result)
        assert 'None' in csv_output or ',' in csv_output
        
        # Markdown should show NULL
        md_output = formatter.to_markdown(result)
        assert 'NULL' in md_output
