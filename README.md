# SQLite Natural Language Query Engine

A tool that converts natural language questions into SQL queries against SQLite databases.

## Features

- 🗣️ **Natural Language Queries** - Ask questions in plain English
- 🔍 **Automatic Schema Extraction** - Understands your database structure
- 🤖 **LLM-Powered** - Uses Claude (Anthropic) by default
- 🔒 **Safe by Default** - READ-ONLY mode, blocks dangerous operations
- 📚 **Domain Knowledge** - Add custom context for better accuracy

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run a query
python main.py --db your_database.db --query "Show all users"

# Interactive mode
python main.py --db your_database.db
```

## Configuration

Edit `config.yaml` to change settings:

```yaml
llm:
  provider: "anthropic"  # anthropic | openai | ollama
  model: "claude-3-5-sonnet-20241022"
```

## Domain Knowledge

Add custom context in the `knowledge/` folder to improve accuracy.
See `knowledge/README.md` for details.
