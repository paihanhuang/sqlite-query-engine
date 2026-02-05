---
trigger: model_decision
---

# LLM Prompt Engineering Protocol

**Goal:** Generate accurate, safe SQLite SQL from natural language queries.
**Role:** You are a Prompt Engineer. Craft prompts that minimize hallucination and maximize SQL correctness.

---

## 1. PROMPT STRUCTURE (The Template)
*Every prompt must follow this structure.*

```
SYSTEM:
You are a SQL expert assistant. Your task is to convert natural language 
questions into valid SQLite SQL queries.

CONTEXT:
[Schema information injected here]

RULES:
[Safety and formatting rules injected here]

USER:
[User's natural language question]

ASSISTANT:
[LLM generates SQL here]
```

---

## 2. SCHEMA INJECTION (Context Engineering)
*How we provide database context to the LLM.*

### A. Schema Format
*Provide structured, parseable schema information.*

```
DATABASE SCHEMA:
Table: employees
  - id (INTEGER, PRIMARY KEY)
  - name (TEXT)
  - department_id (INTEGER, FOREIGN KEY → departments.id)
  - salary (REAL)
  - hire_date (TEXT)

Table: departments
  - id (INTEGER, PRIMARY KEY)
  - name (TEXT)
  - budget (REAL)

RELATIONSHIPS:
  - employees.department_id → departments.id
```

### B. Sample Data (Optional, but Powerful)
*Helps LLM understand data patterns.*

```
SAMPLE DATA (3 rows per table):
employees: [(1, 'Alice', 1, 95000, '2020-01-15'), ...]
departments: [(1, 'Engineering', 500000), ...]
```

### C. Schema Constraints
- Always include PRIMARY KEY annotations
- Always include FOREIGN KEY relationships
- Include column data types (INTEGER, TEXT, REAL, BLOB)
- Limit sample data to 3-5 rows per table

---

## 3. SAFETY RULES (Injection Defense)
*Rules embedded in every prompt.*

```
RULES:
1. Generate ONLY valid SQLite SQL syntax.
2. Return ONLY the SQL query, no explanations unless asked.
3. Use only tables and columns from the provided schema.
4. Do NOT generate INSERT, UPDATE, DELETE, DROP, or ALTER statements.
5. Always include LIMIT clause if not specified (default: 100).
6. Use proper JOIN syntax when crossing tables.
7. Handle NULL values appropriately with IS NULL / IS NOT NULL.
8. Use strftime() for date operations in SQLite.
```

---

## 4. ERROR CORRECTION PROMPT
*When the first query fails, use this template.*

```
The previous SQL query failed with this error:
[ERROR MESSAGE]

Original question: [USER QUESTION]
Failed SQL: [GENERATED SQL]

Please analyze the error and generate a corrected SQL query.
Common fixes:
- Check table/column name spelling
- Verify JOIN conditions
- Ensure proper SQLite function usage
- Check data type compatibility
```

---

## 5. RESULT SUMMARIZATION PROMPT
*Optional: Explain results in natural language.*

```
The user asked: [QUESTION]
The SQL query returned: [RESULT COUNT] rows

Results:
[RESULT DATA]

Provide a brief, natural language summary of these results.
Focus on answering the user's original question directly.
```

---

## 6. PROMPT ANTI-PATTERNS (The Veto List)
*Never do these things.*

1.  **Vague Instructions:**
    - ❌ "Write SQL for the question"
    - ✅ "Generate a SQLite SELECT statement that answers: ..."

2.  **Missing Schema:**
    - ❌ Asking for SQL without providing table/column names
    - ✅ Always include full schema context

3.  **Unbounded Output:**
    - ❌ Allowing unlimited result sets
    - ✅ Enforce LIMIT clause in prompt rules

4.  **Implicit Trust:**
    - ❌ Executing any SQL the LLM generates
    - ✅ Validate SQL is SELECT-only before execution

---

## 7. PROMPT TESTING STRATEGY
*How we verify prompt quality.*

### A. Golden Queries
*Maintain a test set of question → expected SQL pairs.*

| Question | Expected SQL (simplified) |
|----------|--------------------------|
| "List all employees" | `SELECT * FROM employees` |
| "Average salary by department" | `SELECT ... AVG(salary) ... GROUP BY` |
| "Employees hired in 2024" | `SELECT ... strftime('%Y', hire_date) = '2024'` |

### B. Edge Cases
*Test these scenarios explicitly.*
- Questions mentioning non-existent tables
- Ambiguous column references (same name in multiple tables)
- Date/time queries (SQLite date handling)
- NULL value handling
- Aggregate queries without GROUP BY
