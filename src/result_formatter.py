"""
Result Formatter - Format query results for display.

Supports multiple output formats: table, CSV, JSON, markdown.
"""

import csv
import io
import json
from typing import Any

from rich.console import Console
from rich.table import Table

from src.query_executor import QueryResult


class ResultFormatter:
    """Formats query results for different output types."""
    
    def __init__(self):
        self.console = Console()
    
    def to_table(self, result: QueryResult, title: str = "Results") -> None:
        """Display results as a rich table in the terminal."""
        if not result.success:
            self.console.print(f"[red]Error:[/red] {result.error}")
            return
        
        if not result.rows:
            self.console.print("[dim]No results found.[/dim]")
            return
        
        # Create rich table
        table = Table(title=title, show_lines=False)
        
        # Add columns
        for col in result.columns:
            table.add_column(col, style="cyan")
        
        # Add rows
        for row in result.rows:
            table.add_row(*[str(v) if v is not None else "[dim]NULL[/dim]" for v in row])
        
        self.console.print(table)
        self.console.print(f"\n[dim]{result.row_count} row(s) returned[/dim]")
    
    def to_csv(self, result: QueryResult) -> str:
        """Convert results to CSV format."""
        if not result.success:
            return f"Error: {result.error}"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(result.columns)
        
        # Write rows
        for row in result.rows:
            writer.writerow(row)
        
        return output.getvalue()
    
    def to_json(self, result: QueryResult, indent: int = 2) -> str:
        """Convert results to JSON format."""
        if not result.success:
            return json.dumps({"error": result.error}, indent=indent)
        
        # Convert to list of dicts
        data = []
        for row in result.rows:
            row_dict = {}
            for i, col in enumerate(result.columns):
                row_dict[col] = row[i]
            data.append(row_dict)
        
        return json.dumps(data, indent=indent, default=str)
    
    def to_markdown(self, result: QueryResult) -> str:
        """Convert results to Markdown table format."""
        if not result.success:
            return f"**Error:** {result.error}"
        
        if not result.rows:
            return "*No results found.*"
        
        lines = []
        
        # Header row
        lines.append("| " + " | ".join(result.columns) + " |")
        
        # Separator
        lines.append("| " + " | ".join(["---"] * len(result.columns)) + " |")
        
        # Data rows
        for row in result.rows:
            values = [str(v) if v is not None else "NULL" for v in row]
            lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test with mock data
    result = QueryResult(
        success=True,
        columns=["id", "name", "email"],
        rows=[
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
        ],
        row_count=2
    )
    
    formatter = ResultFormatter()
    formatter.to_table(result)
    print("\nCSV:")
    print(formatter.to_csv(result))
    print("\nJSON:")
    print(formatter.to_json(result))
    print("\nMarkdown:")
    print(formatter.to_markdown(result))
