# Domain Knowledge

This folder contains domain-specific knowledge to help the LLM understand your database better.

## How to Use

1. Create `.md` files for each domain/table group
2. Document cryptic column names, business rules, and common queries
3. Use `_joins.md` for complex cross-table join recipes

## Example Structure

```
knowledge/
├── README.md           # This file
├── _joins.md           # Cross-domain join patterns
├── transactions.md     # Financial tables
├── users.md            # User/account tables
└── products.md         # Product catalog tables
```

## File Format

Write in plain Markdown:

```markdown
# Transactions

## Key Concepts

### Transaction Codes
- D = Debit (money out)
- C = Credit (money in)

## Business Rules
- "Revenue" = sum of Credit transactions
```
