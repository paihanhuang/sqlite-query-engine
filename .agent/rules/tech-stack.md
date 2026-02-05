---
trigger: always_on
---

# Technology Stack & Constraints

**Core Principle:** Use the simplest tool that gets the job done.
**Default Language:** Python 3.10+ (Type Hinting required).

---

## 1. RUNTIME LIBRARIES (The "Boring" Stack)
*You may use these libraries without asking. All others require justification in a Design RFC.*

### Database & Schema
- **`sqlite3` (standard lib):** Primary interface for SQLite database operations.
    - *Why:* Built-in, zero dependencies, perfect for our use case.
- **`pydantic`:** MANDATORY for all data validation and schema definition.
    - *Why:* Enforces type safety for schema metadata and query results.

### AI Interaction
- **Native SDKs only:** (`openai`, `anthropic`, or `ollama`)
- **STRICTLY PROHIBITED:** Do not use `LangChain`, `LlamaIndex`, `CrewAI`, or other "Orchestration Frameworks."
    - *Rationale:* These libraries hide prompt logic and control flow. We require explicit, debuggable, standard Python code for all AI interactions.

### CLI & Display
- **`rich`:** For beautiful terminal tables and progress indicators.
- **`argparse` (standard lib):** For CLI argument parsing.
- **`pyyaml`:** For configuration file parsing.

---

## 2. TESTING & QUALITY (The V-Model Enforcer)
*Tools required to verify the Design Protocol.*

- **`pytest`:** The standard test runner.
- **`pytest-mock`:** For isolating unit tests (mocking LLM API calls).

---

## 3. INFRASTRUCTURE (YAGNI)
*Adhere to the "Steel Thread" philosophy.*

- **Storage:** File-based storage (YAML config, SQLite database) for all phases.
- **Containerization:** Do NOT create Dockerfiles until Application Logic is fully verified (Phase 3).
- **Web UI:** Defer until CLI is fully functional and tested.

---

## 4. DEVELOPMENT TOOLING
*Keep the developer experience fast and strict.*

- **Linting & Formatting:** `ruff`
    - *Config:* Aggressive ruleset to enforce clean code.
- **Type Checking:** `mypy` (recommended but not mandatory for v1)
- **Dependency Management:** `pip` with `requirements.txt` (keep it simple for v1)
