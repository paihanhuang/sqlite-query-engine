#!/usr/bin/env python3
"""
SQLite Query Engine - Natural Language to SQL

A tool that converts natural language questions into SQL queries
against SQLite databases using LLM (Anthropic Claude by default).
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from src.schema_extractor import SchemaExtractor
from src.llm_service import create_llm_service

console = Console()


# System prompt for SQL generation
SYSTEM_PROMPT = """You are a SQL expert assistant. Your task is to convert natural language questions into valid SQLite SQL queries.

RULES:
1. Generate ONLY valid SQLite SQL syntax.
2. Return ONLY the SQL query, no explanations.
3. Use only tables and columns from the provided schema.
4. Do NOT generate INSERT, UPDATE, DELETE, DROP, or ALTER statements.
5. Always include LIMIT clause if not specified (default: 100).
6. Use proper JOIN syntax when crossing tables.
7. Handle NULL values appropriately with IS NULL / IS NOT NULL.
8. Use strftime() for date operations in SQLite.

Return ONLY the SQL query, nothing else."""


def main():
    parser = argparse.ArgumentParser(
        description="Natural Language to SQL Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--db", "-d",
        required=True,
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--query", "-q",
        help="Natural language question (if not provided, enters interactive mode)"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )
    parser.add_argument(
        "--sql-only",
        action="store_true",
        help="Only show generated SQL, don't execute"
    )
    
    args = parser.parse_args()
    
    # Validate database exists
    db_path = Path(args.db)
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database file not found: {db_path}")
        sys.exit(1)
    
    # Extract schema
    console.print(f"\n🔍 [bold]Analyzing database schema...[/bold]")
    try:
        extractor = SchemaExtractor(db_path)
        schema = extractor.extract()
        
        table_count = len(schema.tables)
        table_names = [t.name for t in schema.tables]
        console.print(f"   Found {table_count} tables: {', '.join(table_names)}")
    except Exception as e:
        console.print(f"[red]Error extracting schema:[/red] {e}")
        sys.exit(1)
    
    # Initialize LLM service
    try:
        llm = create_llm_service(args.config)
        console.print(f"   Using LLM: [cyan]{llm.model if hasattr(llm, 'model') else 'configured model'}[/cyan]")
    except Exception as e:
        console.print(f"[red]Error initializing LLM:[/red] {e}")
        sys.exit(1)
    
    # Build prompt with schema
    schema_context = schema.to_prompt_string()
    
    if args.query:
        # Single query mode
        process_query(args.query, schema_context, llm, args.sql_only)
    else:
        # Interactive mode
        interactive_mode(schema_context, llm, args.sql_only)


def process_query(question: str, schema_context: str, llm, sql_only: bool = False):
    """Process a single natural language query."""
    
    # Build the full prompt
    prompt = f"""{schema_context}

USER QUESTION: {question}

SQL:"""
    
    console.print(f"\n💬 [bold]Question:[/bold] {question}")
    
    try:
        # Call LLM
        response = llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        sql = response.content.strip()
        
        # Remove markdown code blocks if present
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
            sql = sql.strip()
        
        # Display generated SQL
        console.print("\n🤖 [bold]Generated SQL:[/bold]")
        syntax = Syntax(sql, "sql", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, border_style="green"))
        
        if sql_only:
            return sql
        
        # TODO: Phase 2 - Execute query and display results
        console.print("\n[dim]Query execution will be implemented in Phase 2[/dim]")
        
        return sql
        
    except Exception as e:
        console.print(f"\n[red]Error generating SQL:[/red] {e}")
        return None


def interactive_mode(schema_context: str, llm, sql_only: bool = False):
    """Run interactive query mode."""
    
    console.print("\n💬 [bold]Interactive Mode[/bold] (type 'exit' or 'quit' to leave)")
    console.print("[dim]Ask questions in natural language...[/dim]\n")
    
    while True:
        try:
            question = console.input("[bold green]>[/bold green] ")
            
            if question.lower() in ("exit", "quit", "q"):
                console.print("\n👋 Goodbye!")
                break
            
            if not question.strip():
                continue
            
            process_query(question, schema_context, llm, sql_only)
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
