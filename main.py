#!/usr/bin/env python3
"""
SQLite Query Engine - Natural Language to SQL

A tool that converts natural language questions into SQL queries
against SQLite databases using LLM (Anthropic Claude by default).
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from src.schema_extractor import SchemaExtractor
from src.knowledge_loader import KnowledgeLoader
from src.prompt_builder import PromptBuilder
from src.llm_service import create_llm_service
from src.query_executor import QueryExecutor
from src.result_formatter import ResultFormatter

console = Console()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


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
    parser.add_argument(
        "--format", "-f",
        choices=["table", "csv", "json", "markdown"],
        default="table",
        help="Output format (default: table)"
    )
    parser.add_argument(
        "--knowledge", "-k",
        default="knowledge",
        help="Path to knowledge directory (default: knowledge)"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
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
        
        table_names = [t.name for t in schema.tables]
        console.print(f"   Found {len(table_names)} tables: {', '.join(table_names)}")
    except Exception as e:
        console.print(f"[red]Error extracting schema:[/red] {e}")
        sys.exit(1)
    
    # Initialize knowledge loader
    knowledge_loader = KnowledgeLoader(args.knowledge)
    if knowledge_loader.exists():
        knowledge_files = knowledge_loader.list_files()
        if knowledge_files:
            console.print(f"   📚 Knowledge files: {', '.join(f.name for f in knowledge_files)}")
    
    # Initialize LLM service
    try:
        llm = create_llm_service(args.config)
        model_name = getattr(llm, 'model', 'configured model')
        console.print(f"   🤖 Using LLM: [cyan]{model_name}[/cyan]")
    except Exception as e:
        console.print(f"[red]Error initializing LLM:[/red] {e}")
        sys.exit(1)
    
    # Initialize other components
    prompt_builder = PromptBuilder(schema)
    query_executor = QueryExecutor(
        db_path,
        read_only=config.get("safety", {}).get("read_only", True),
        timeout=config.get("safety", {}).get("query_timeout", 30),
        max_results=config.get("safety", {}).get("max_results", 1000)
    )
    formatter = ResultFormatter()
    max_retries = config.get("safety", {}).get("max_retries", 3)
    
    if args.query:
        # Single query mode
        process_query(
            args.query, 
            prompt_builder, 
            llm, 
            query_executor, 
            formatter,
            knowledge_loader,
            table_names,
            args.sql_only,
            args.format,
            max_retries
        )
    else:
        # Interactive mode
        interactive_mode(
            prompt_builder, 
            llm, 
            query_executor, 
            formatter,
            knowledge_loader,
            table_names,
            args.sql_only,
            args.format,
            max_retries
        )


def process_query(question: str, prompt_builder: PromptBuilder, llm, 
                  executor: QueryExecutor, formatter: ResultFormatter,
                  knowledge_loader: KnowledgeLoader, table_names: list[str],
                  sql_only: bool = False, output_format: str = "table",
                  max_retries: int = 3) -> str:
    """Process a single natural language query with retry loop."""
    
    console.print(f"\n💬 [bold]Question:[/bold] {question}")
    
    # Get relevant knowledge context
    knowledge_context = knowledge_loader.get_context(question, table_names)
    if knowledge_context:
        console.print("[dim]   (domain knowledge loaded)[/dim]")
    
    error_context = None
    
    for attempt in range(max_retries):
        try:
            # Build prompt
            prompt = prompt_builder.build_query_prompt(
                question, 
                knowledge_context=knowledge_context,
                error_context=error_context
            )
            
            # Call LLM
            response = llm.generate(prompt, system_prompt=prompt_builder.get_system_prompt())
            sql = response.content.strip()
            
            # Remove markdown code blocks if present
            if sql.startswith("```"):
                lines = sql.split("\n")
                sql = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                sql = sql.strip()
            
            # Display generated SQL
            console.print(f"\n🤖 [bold]Generated SQL:[/bold]")
            syntax = Syntax(sql, "sql", theme="monokai", line_numbers=False)
            console.print(Panel(syntax, border_style="green"))
            
            if sql_only:
                return sql
            
            # Execute query
            result = executor.execute(sql)
            
            if result.success:
                # Display results
                console.print()
                if output_format == "table":
                    formatter.to_table(result)
                elif output_format == "csv":
                    console.print(formatter.to_csv(result))
                elif output_format == "json":
                    console.print(formatter.to_json(result))
                elif output_format == "markdown":
                    console.print(formatter.to_markdown(result))
                
                return sql
            else:
                # Query failed - prepare for retry
                if attempt < max_retries - 1:
                    console.print(f"\n[yellow]⚠️ Query failed: {result.error}[/yellow]")
                    console.print(f"[dim]   Retrying ({attempt + 2}/{max_retries})...[/dim]")
                    error_context = prompt_builder.build_error_context(sql, result.error)
                else:
                    console.print(f"\n[red]❌ Query failed after {max_retries} attempts:[/red] {result.error}")
                    return None
            
        except Exception as e:
            if attempt < max_retries - 1:
                console.print(f"\n[yellow]⚠️ Error: {e}[/yellow]")
                console.print(f"[dim]   Retrying ({attempt + 2}/{max_retries})...[/dim]")
                error_context = f"Error: {str(e)}"
            else:
                console.print(f"\n[red]❌ Failed after {max_retries} attempts:[/red] {e}")
                return None
    
    return None


def interactive_mode(prompt_builder: PromptBuilder, llm, 
                     executor: QueryExecutor, formatter: ResultFormatter,
                     knowledge_loader: KnowledgeLoader, table_names: list[str],
                     sql_only: bool = False, output_format: str = "table",
                     max_retries: int = 3):
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
            
            process_query(
                question, 
                prompt_builder, 
                llm, 
                executor, 
                formatter,
                knowledge_loader,
                table_names,
                sql_only,
                output_format,
                max_retries
            )
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
