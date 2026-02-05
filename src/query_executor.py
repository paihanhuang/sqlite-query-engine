"""
Query Executor - Safe SQL execution with validation.

Executes generated SQL against SQLite databases with safety checks,
timeout protection, and error handling.
"""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class QueryResult:
    """Result of a SQL query execution."""
    success: bool
    columns: list[str]
    rows: list[tuple]
    row_count: int
    error: Optional[str] = None
    sql: Optional[str] = None


class QueryExecutor:
    """Safely executes SQL queries against a SQLite database."""
    
    # SQL statements that modify data (blocked in read-only mode)
    WRITE_PATTERNS = [
        r'\bINSERT\b',
        r'\bUPDATE\b', 
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bALTER\b',
        r'\bCREATE\b',
        r'\bTRUNCATE\b',
        r'\bREPLACE\b',
    ]
    
    def __init__(self, db_path: str | Path, read_only: bool = True, 
                 timeout: int = 30, max_results: int = 1000):
        """
        Initialize the query executor.
        
        Args:
            db_path: Path to SQLite database file
            read_only: If True, block all write operations
            timeout: Query timeout in seconds
            max_results: Maximum number of rows to return
        """
        self.db_path = Path(db_path)
        self.read_only = read_only
        self.timeout = timeout
        self.max_results = max_results
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def is_safe_query(self, sql: str) -> tuple[bool, str]:
        """
        Check if a SQL query is safe to execute.
        
        Returns:
            Tuple of (is_safe, error_message)
        """
        sql_upper = sql.upper().strip()
        
        # Check for write operations in read-only mode
        if self.read_only:
            for pattern in self.WRITE_PATTERNS:
                if re.search(pattern, sql_upper):
                    return False, f"Write operation blocked in read-only mode: {pattern}"
        
        # Check for multiple statements (potential injection)
        # Allow semicolons only at the end
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements not allowed"
        
        return True, ""
    
    def execute(self, sql: str) -> QueryResult:
        """
        Execute a SQL query and return results.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            QueryResult with columns, rows, and metadata
        """
        # Validate query safety
        is_safe, error_msg = self.is_safe_query(sql)
        if not is_safe:
            return QueryResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                error=error_msg,
                sql=sql
            )
        
        # Clean up SQL
        sql = sql.strip()
        if sql.endswith(';'):
            sql = sql[:-1]
        
        # Add LIMIT if not present and this is a SELECT
        if sql.upper().startswith('SELECT') and 'LIMIT' not in sql.upper():
            sql = f"{sql} LIMIT {self.max_results}"
        
        try:
            # Connect with timeout
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(sql)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results (limited)
            rows = cursor.fetchmany(self.max_results)
            rows = [tuple(row) for row in rows]
            
            conn.close()
            
            return QueryResult(
                success=True,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                sql=sql
            )
            
        except sqlite3.Error as e:
            return QueryResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                error=str(e),
                sql=sql
            )
        except Exception as e:
            return QueryResult(
                success=False,
                columns=[],
                rows=[],
                row_count=0,
                error=f"Unexpected error: {str(e)}",
                sql=sql
            )


if __name__ == "__main__":
    # Simple test
    import sys
    if len(sys.argv) > 2:
        executor = QueryExecutor(sys.argv[1])
        result = executor.execute(sys.argv[2])
        if result.success:
            print(f"Columns: {result.columns}")
            print(f"Rows: {result.row_count}")
            for row in result.rows[:5]:
                print(row)
        else:
            print(f"Error: {result.error}")
    else:
        print("Usage: python query_executor.py <database.db> <SQL>")
