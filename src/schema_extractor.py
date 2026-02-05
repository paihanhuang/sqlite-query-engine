"""
Schema Extractor - Extract database structure from SQLite files.

Extracts tables, columns, data types, primary keys, and foreign key relationships.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Column:
    """Represents a database column."""
    name: str
    data_type: str
    is_primary_key: bool = False
    is_nullable: bool = True


@dataclass
class ForeignKey:
    """Represents a foreign key relationship."""
    from_table: str
    from_column: str
    to_table: str
    to_column: str


@dataclass
class Table:
    """Represents a database table."""
    name: str
    columns: list[Column]
    primary_keys: list[str]
    foreign_keys: list[ForeignKey]


@dataclass
class Schema:
    """Represents the complete database schema."""
    tables: list[Table]
    foreign_keys: list[ForeignKey]
    
    def to_prompt_string(self) -> str:
        """Convert schema to a string suitable for LLM prompt."""
        lines = ["DATABASE SCHEMA:", ""]
        
        for table in self.tables:
            # Table header
            pk_cols = [c.name for c in table.columns if c.is_primary_key]
            lines.append(f"Table: {table.name}")
            
            # Columns
            for col in table.columns:
                pk_marker = " (PRIMARY KEY)" if col.is_primary_key else ""
                nullable = "" if col.is_nullable else " NOT NULL"
                lines.append(f"  - {col.name} ({col.data_type}{pk_marker}{nullable})")
            
            lines.append("")
        
        # Foreign key relationships
        if self.foreign_keys:
            lines.append("RELATIONSHIPS:")
            for fk in self.foreign_keys:
                lines.append(f"  - {fk.from_table}.{fk.from_column} → {fk.to_table}.{fk.to_column}")
            lines.append("")
        
        return "\n".join(lines)


class SchemaExtractor:
    """Extracts schema information from a SQLite database."""
    
    def __init__(self, db_path: str | Path):
        """Initialize with path to SQLite database file."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def extract(self) -> Schema:
        """Extract complete schema from the database."""
        conn = sqlite3.connect(self.db_path)
        try:
            tables = self._extract_tables(conn)
            all_foreign_keys = []
            for table in tables:
                all_foreign_keys.extend(table.foreign_keys)
            return Schema(tables=tables, foreign_keys=all_foreign_keys)
        finally:
            conn.close()
    
    def _extract_tables(self, conn: sqlite3.Connection) -> list[Table]:
        """Extract all tables from the database."""
        cursor = conn.cursor()
        
        # Get all table names (exclude sqlite internal tables)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        tables = []
        for table_name in table_names:
            columns = self._extract_columns(conn, table_name)
            foreign_keys = self._extract_foreign_keys(conn, table_name)
            primary_keys = [c.name for c in columns if c.is_primary_key]
            
            tables.append(Table(
                name=table_name,
                columns=columns,
                primary_keys=primary_keys,
                foreign_keys=foreign_keys
            ))
        
        return tables
    
    def _extract_columns(self, conn: sqlite3.Connection, table_name: str) -> list[Column]:
        """Extract columns for a specific table."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        
        columns = []
        for row in cursor.fetchall():
            # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
            columns.append(Column(
                name=row[1],
                data_type=row[2] or "TEXT",
                is_nullable=not bool(row[3]),
                is_primary_key=bool(row[5])
            ))
        
        return columns
    
    def _extract_foreign_keys(self, conn: sqlite3.Connection, table_name: str) -> list[ForeignKey]:
        """Extract foreign key relationships for a specific table."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
        
        foreign_keys = []
        for row in cursor.fetchall():
            # PRAGMA foreign_key_list returns: id, seq, table, from, to, on_update, on_delete, match
            foreign_keys.append(ForeignKey(
                from_table=table_name,
                from_column=row[3],
                to_table=row[2],
                to_column=row[4]
            ))
        
        return foreign_keys
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> list[dict]:
        """Get sample rows from a table for context."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM '{table_name}' LIMIT {limit}")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


if __name__ == "__main__":
    # Simple test
    import sys
    if len(sys.argv) > 1:
        extractor = SchemaExtractor(sys.argv[1])
        schema = extractor.extract()
        print(schema.to_prompt_string())
    else:
        print("Usage: python schema_extractor.py <database.db>")
