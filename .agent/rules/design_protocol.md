---
trigger: model_decision
---

# Engineering Design Protocol (RFC Standard)

**Trigger:** When the user asks for a "Design," "Proposal," or "Plan."
**Goal:** Eliminate ambiguity and ensure verification symmetry (V-Model).
**Output Constraint:** Do not write implementation code until this document is explicitly APPROVED by the user.

---

## 1. EXECUTIVE SUMMARY & CONSTRAINTS
*Define the box we are working in.*

### A. Context & Assumptions
*List what we know and what we are guessing.*
- **Goal:** (e.g., "Convert natural language question to SQL query")
- **Inputs:** (e.g., "SQLite database file, user question string")
- **Environment:** (e.g., "Requires LLM API access, runs locally")
- **Unknowns:** (e.g., "Database schema complexity varies by user")

### B. Requirements Analysis (V-Model Level 1)
*Translate vague user goals into strict Pass/Fail criteria.*
- **User Story:** "As a user, I want to ask questions in plain English and get results from my database."
- **Acceptance Criteria (The "Definition of Done"):**
    1.  [ ] System extracts and understands database schema.
    2.  [ ] System generates valid SQLite SQL from natural language.
    3.  [ ] System executes query and returns formatted results.

---

## 2. PROPOSED SOLUTION (The "How")
*Detailed engineering specifications.*

### A. Algorithm & Logic
*Plain English explanation of the core logic. No code yet.*
- **Step 1:** Extract schema (tables, columns, relationships) from SQLite
- **Step 2:** Build context-aware prompt with schema + user question
- **Step 3:** Call LLM to generate SQL
- **Step 4:** Validate and execute SQL safely
- **Step 5:** Format and display results

### B. Data Flow & Architecture
*How data moves through the system.*
- **Input:** User question + SQLite database path
- **Transformation:** NL → Prompt → LLM → SQL → Execution → Results
- **Output:** Formatted table/JSON/CSV

### C. Technology Stack & Rationale
*Why are we using these tools?*
- Refer to `.agent/rules/tech-stack.md` for approved libraries.
- Any deviation requires explicit justification.

---

## 3. VERIFICATION PLAN (The V-Model Symmetry)
*How we prove it works at every level.*

### A. Integration Testing (V-Model Level 2)
*How do modules connect?*
- **Test:** End-to-end flow from question → SQL → results
- **Sample Database:** Create test.db with known data for reproducible tests

### B. Unit Testing (V-Model Level 3)
*Low-level correctness.*
- **Schema Extractor:** Test with various SQLite schemas
- **Query Executor:** Test SQL validation, safety checks
- **Result Formatter:** Test output format correctness

---

## 4. PHASED IMPLEMENTATION PLAN
*We start small and verifiable.*

### Phase 1: Steel Thread (Walking Skeleton)
*Goal: Prove the plumbing works.*
- **Scope:** Load database, extract schema, print schema, call LLM with dummy prompt.
- **Verification:** See schema printed, LLM responds.

### Phase 2: MVP (Core Logic)
*Goal: Solve the Happy Path.*
- **Scope:** Full NL → SQL → Results pipeline for simple queries.
- **Verification:** Query "List all X" returns correct data.

### Phase 3: Robustness
*Goal: Production ready.*
- **Scope:** Error handling, retry logic, complex queries with JOINs.
- **Verification:** Handle malformed questions, invalid SQL regeneration.

---

## 5. MINIMALISM CHECK (Self-Correction)
*Before submitting this proposal, answer these questions:*
1.  **Is this the simplest way?** (If No, simplify Section 2).
2.  **Did I add any library not in `tech-stack.md`?** (If Yes, justify strictly in Section 2C).
3.  **Does this duplicate existing functionality?** (If Yes, reuse existing code).
