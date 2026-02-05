"""
Prompt Builder - Construct prompts for the LLM.

Combines schema, domain knowledge, and user question into
effective prompts for SQL generation.
"""

from typing import Optional

from src.schema_extractor import Schema


# System prompt for SQL generation
SYSTEM_PROMPT = """You are a SQL expert assistant. Your task is to convert natural language questions into valid SQLite SQL queries.

RULES:
1. Generate ONLY valid SQLite SQL syntax.
2. Return ONLY the SQL query, no explanations or markdown formatting.
3. Use only tables and columns from the provided schema.
4. Do NOT generate INSERT, UPDATE, DELETE, DROP, or ALTER statements.
5. Always include LIMIT clause if not specified (default: 100).
6. Use proper JOIN syntax when crossing tables.
7. Handle NULL values appropriately with IS NULL / IS NOT NULL.
8. Use strftime() for date operations in SQLite.
9. Pay close attention to any DOMAIN KNOWLEDGE provided - it contains critical business logic.

Return ONLY the SQL query, nothing else. No ```sql blocks, no explanations."""


class PromptBuilder:
    """Builds prompts for the LLM."""
    
    def __init__(self, schema: Schema):
        """
        Initialize with database schema.
        
        Args:
            schema: Extracted database schema
        """
        self.schema = schema
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return SYSTEM_PROMPT
    
    def build_query_prompt(self, question: str, 
                           knowledge_context: Optional[str] = None,
                           error_context: Optional[str] = None) -> str:
        """
        Build a complete prompt for SQL generation.
        
        Args:
            question: User's natural language question
            knowledge_context: Optional domain knowledge to include
            error_context: Optional previous error for retry
            
        Returns:
            Complete prompt string
        """
        parts = []
        
        # Add schema
        parts.append(self.schema.to_prompt_string())
        
        # Add domain knowledge if available
        if knowledge_context:
            parts.append(knowledge_context)
        
        # Add error context if retrying
        if error_context:
            parts.append("PREVIOUS ATTEMPT FAILED:")
            parts.append(error_context)
            parts.append("")
            parts.append("Please generate a corrected SQL query.")
            parts.append("")
        
        # Add user question
        parts.append(f"USER QUESTION: {question}")
        parts.append("")
        parts.append("SQL:")
        
        return "\n".join(parts)
    
    def build_error_context(self, sql: str, error: str) -> str:
        """
        Build error context for retry attempts.
        
        Args:
            sql: The SQL that failed
            error: The error message
            
        Returns:
            Error context string
        """
        return f"SQL: {sql}\nError: {error}"


if __name__ == "__main__":
    # Test with mock schema
    from src.schema_extractor import Table, Column
    
    schema = Schema(
        tables=[
            Table(
                name="users",
                columns=[Column("id", "INTEGER", is_primary_key=True)],
                primary_keys=["id"],
                foreign_keys=[]
            )
        ],
        foreign_keys=[]
    )
    
    builder = PromptBuilder(schema)
    prompt = builder.build_query_prompt("List all users")
    print(prompt)
