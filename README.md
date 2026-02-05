# SQLite Natural Language Query Engine

A tool that converts natural language questions into SQL queries against SQLite databases using LLM (Anthropic Claude).

## Features

- 🗣️ **Natural Language Queries** - Ask questions in plain English
- 🔍 **Automatic Schema Extraction** - Understands your database structure and relationships
- 🤖 **LLM-Powered** - Uses Claude (Anthropic) by default, supports OpenAI and Ollama
- 🔒 **Safe by Default** - READ-ONLY mode, blocks INSERT/UPDATE/DELETE
- 📚 **Domain Knowledge** - Add custom context for better accuracy
- 🔄 **Error Retry** - LLM auto-corrects failed SQL (up to 3 attempts)
- 📊 **Multiple Formats** - Table, CSV, JSON, Markdown output

## Quick Start

```bash
# Clone and setup
git clone https://github.com/paihanhuang/sqlite-query-engine.git
cd sqlite-query-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run a query
python main.py --db your_database.db --query "Show all users"

# Interactive mode
python main.py --db your_database.db
```

## Usage Examples

```bash
# Simple query
python main.py --db data.db --query "List all users"

# Complex JOIN query
python main.py --db data.db --query "Show average salary by department"

# Different output formats
python main.py --db data.db --query "Show users" --format json
python main.py --db data.db --query "Show users" --format csv
python main.py --db data.db --query "Show users" --format markdown

# SQL only (no execution)
python main.py --db data.db --query "Show users" --sql-only
```

## Configuration

Edit `config.yaml` to change settings:

```yaml
llm:
  provider: "anthropic"  # anthropic | openai | ollama
  model: "claude-sonnet-4-20250514"
  temperature: 0.0  # Deterministic for SQL

safety:
  read_only: true
  query_timeout: 30
  max_results: 1000
  max_retries: 3

output:
  format: "table"  # table | csv | json | markdown
```

## Domain Knowledge

Add custom context in the `knowledge/` folder to improve accuracy for domain-specific queries.

**Structure:**
```
knowledge/
├── README.md           # Database overview
├── _joins.md           # Cross-domain join recipes
├── transactions.md     # Financial tables
└── users.md            # User tables
```

**Example (`knowledge/transactions.md`):**
```markdown
# Transactions

## Key Concepts
- txn_cd: D = Debit, C = Credit
- amt: Amount stored in cents (divide by 100 for dollars)

## Business Rules
- "Revenue" means sum of Credit transactions (txn_cd = 'C')
```

## Architecture

```
User Question → Schema Extractor → Knowledge Loader → Prompt Builder
                                                          ↓
                                                         LLM
                                                          ↓
              Result Formatter ← Query Executor ← SQL Validator
```

## Testing

```bash
# Run all tests
PYTHONPATH=. ./venv/bin/python -m pytest tests/ -v -p no:launch_testing

# Results: 34 tests covering all modules
```

## Project Structure

```
sqlite-query-engine/
├── src/
│   ├── schema_extractor.py    # Extract tables/columns/FKs
│   ├── knowledge_loader.py    # Load domain knowledge
│   ├── prompt_builder.py      # Build LLM prompts
│   ├── llm_service.py         # Anthropic/OpenAI/Ollama
│   ├── query_executor.py      # Safe SQL execution
│   └── result_formatter.py    # Table/CSV/JSON output
├── tests/                     # Unit tests (34 total)
├── knowledge/                 # Domain knowledge files
├── config.yaml                # Configuration
├── main.py                    # CLI entry point
└── requirements.txt
```

## License

MIT
