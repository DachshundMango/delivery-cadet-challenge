# System Architecture

This document provides a comprehensive overview of Delivery Cadet's system design, component structure, and data flow.

## Table of Contents
- [Project Structure](#project-structure)
- [High-Level Architecture](#high-level-architecture)
- [LangGraph Workflow](#langgraph-workflow)
- [Key Components](#key-components)
- [Data Flow](#data-flow)
- [Dataset-Agnostic Design](#dataset-agnostic-design)
- [Module Responsibilities](#module-responsibilities)

---

## Project Structure

```
cadet/
├── src/                          # Python backend source code (3,872 LOC)
│   ├── agent/                    # LangGraph agent workflow (1,503 LOC)
│   │   ├── __init__.py           # Public API exports
│   │   ├── graph.py              # LangGraph workflow definition (95 LOC)
│   │   ├── nodes.py              # Agent node implementations (791 LOC)
│   │   ├── prompts.py            # LLM prompt templates (517 LOC)
│   │   ├── feedbacks.py          # Error feedback messages (268 LOC) 🆕
│   │   └── state.py              # State management schema (60 LOC)
│   │
│   ├── data_pipeline/            # ETL and data preparation (1,606 LOC)
│   │   ├── __init__.py           # Public API exports
│   │   ├── profiler.py           # CSV data profiler (91 LOC)
│   │   ├── relationship_discovery.py  # Automatic FK detection (226 LOC)
│   │   ├── integrity_checker.py  # Data validation utilities (261 LOC)
│   │   ├── load_data.py          # CSV to DB ETL pipeline (167 LOC)
│   │   ├── transform_data.py     # Interactive data transformation (231 LOC)
│   │   ├── pii_discovery.py      # LLM-based PII column detection (189 LOC)
│   │   ├── generate_schema.py    # Schema + PII metadata generator (226 LOC)
│   │   └── setup.py              # Automated pipeline orchestrator (190 LOC)
│   │
│   ├── core/                     # Shared utilities (588 LOC)
│   │   ├── __init__.py           # Public API exports
│   │   ├── console.py            # Unified CLI output formatting (72 LOC)
│   │   ├── db.py                 # Database connection management (84 LOC)
│   │   ├── logger.py             # Logging configuration (44 LOC)
│   │   ├── errors.py             # Custom exception classes (55 LOC)
│   │   └── validation.py         # SQL validation & security (302 LOC)
│   │
│   ├── config/                   # Configuration and metadata
│   │   ├── keys.json             # PK/FK metadata configuration
│   │   ├── schema_info.json      # Generated schema (used by LLM)
│   │   ├── schema_info.md        # Human-readable schema docs
│   │   └── data_profile.json     # Data profiling statistics
│   │
│   ├── setup.py                  # Automated pipeline orchestrator
│   ├── reset_db.py               # Database + config reset utility
│   └── cli.py                    # CLI entry point
│
├── frontend/                     # Next.js 15 + React 19 frontend
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   ├── components/           # React components
│   │   │   ├── plotly-chart.tsx  # Plotly visualization
│   │   │   └── python-runner.tsx # Pyodide runtime
│   │   ├── providers/            # Context providers & LangGraph client
│   │   └── hooks/                # Custom React hooks
│   ├── package.json
│   └── tailwind.config.js
│
├── data/                         # CSV data files (8 files)
│   ├── sales_customers.csv
│   ├── sales_franchises.csv
│   ├── sales_suppliers.csv
│   ├── sales_transactions.csv
│   ├── media_customer_reviews.csv
│   ├── media_gold_reviews_chunked.csv
│   ├── media_campaigns.csv
│   └── missing_suppliers.csv
│
├── docs/                         # Documentation
│   ├── ERROR-HANDLING.md         # Error handling & retry logic
│   ├── ARCHITECTURE.md           # This file
│   └── sql.md                    # SQL patterns & examples
│
├── tests/                        # Testing
│   └── test_security.py          # Security validation tests
│
├── docker-compose.yaml           # PostgreSQL + PgAdmin
├── langgraph.json                # LangGraph configuration
├── start.sh                      # One-command startup script
├── environment.yml               # Conda environment (cross-platform)
├── requirements.txt              # Python dependencies (pip)
├── .env                          # Environment variables
└── README.md                     # User-facing documentation
```

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                       │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ ChatGPT-style  │  │ Plotly Chart │  │ Pyodide (Python)   │  │
│  │ UI (React 19)  │  │ Renderer     │  │ Runtime (Pandas)   │  │
│  └────────┬───────┘  └──────┬───────┘  └──────┬─────────────┘  │
│           │                  │                  │                 │
│           └──────────────────┼──────────────────┘                │
│                              │                                    │
└──────────────────────────────┼────────────────────────────────────┘
                               │ HTTP/WebSocket (Streaming)
                               │
┌──────────────────────────────┼────────────────────────────────────┐
│                              ▼                                     │
│                    LangGraph Server (Port 2024)                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              LangGraph State Machine (graph.py)             │ │
│  │  ┌───────────┐  ┌─────────┐  ┌──────────┐  ┌─────────────┐│ │
│  │  │Intent     │→ │SQL Gen  │→ │Validation│→ │Execution    ││ │
│  │  │Classifier │  │(LLM)    │  │(Security)│  │(PostgreSQL) ││ │
│  │  └───────────┘  └─────────┘  └──────────┘  └─────────────┘│ │
│  │                       ↓                           ↓          │ │
│  │                  ┌─────────┐               ┌──────────┐     │ │
│  │                  │Feedback │←─ Error? ────│Check     │     │ │
│  │                  │(Retry)  │               │Result    │     │ │
│  │                  └─────────┘               └──────────┘     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  LLM Provider (Cerebras)                     │ │
│  │              llama-3.3-70b (OpenAI-compatible API)          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 15 Database                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐│
│  │ Customers  │  │ Orders     │  │ Products   │  │ Reviews   ││
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └─────┬─────┘│
│         └────────────────┴────────────────┴───────────────┘     │
│                      Foreign Key Constraints                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## LangGraph Workflow

### State Machine Diagram

```
┌─────────────┐
│    START    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ read_question   │  Extract user question from messages
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ intent_classification│  Classify as "sql" or "general"
└──────────┬───────────┘  (Temperature: 0.0 - deterministic)
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌──────────────────────────────┐  ┌─────────────────────────┐
│pyodide_request_              │  │generate_general_response│
│      classification          │  └───────────┬─────────────┘
│                              │              │ (Temperature: 0.7)
│ Check for analysis keywords  │              ▼
└───────────┬──────────────────┘           ┌─────┐
            │                              │ END │
      ┌─────┴──────┐                       └─────┘
      │            │
      ▼            ▼
 [needs_     [skip_
  pyodide]    pyodide]
      │            │
      └────┬───────┘
           ▼
      ┌───────────┐
      │generate_  │  Uses simple SQL (pyodide=True)
      │   SQL     │  or complex SQL (pyodide=False)
      └─────┬─────┘  (Temperature: 0.1 - accurate)
            │
            ▼
      ┌───────────┐
      │execute_SQL│
      └─────┬─────┘
            │
        ┌───┴───┐
        │ Error?│  (check_query_validation)
        └───┬───┘
            │
        ┌───┴───────┐
        │           │
        ▼           ▼
    [retry]     [success]
        │           │
        │           ▼
        │     ┌──────────────────────────────┐
        │     │visualisation_request_        │
        │     │      classification          │  Keyword-based chart detection
        │     └───────────┬──────────────────┘  (Temperature: 0.0 - strict)
        │                 │
        │           ┌─────┴──────┐
        │           │            │
        │           ▼            ▼
        │     [needs_viz]    [skip_viz]
        │           │            │
        │           └─────┬──────┘
        │                 │
        │                 ▼
        │     ┌──────────────────────────────┐
        │     │Check needs_pyodide from      │
        │     │     earlier classification   │
        │     └───────────┬──────────────────┘
        │                 │
        │           ┌─────┴──────┐
        │           │            │
        │           ▼            ▼
        │    [needs_pyodide] [skip]
        │           │            │
        │           ▼            │
        │  ┌─────────────────┐  │
        │  │generate_pyodide_│  │  Generate pandas analysis code
        │  │    analysis     │  │
        │  └────────┬────────┘  │
        │           │            │
        │           └────┬───────┘
        │                ▼
        │           ┌───────────────┐
        │           │generate_      │
        │           │  response     │  Format natural language answer
        │           └───────┬───────┘  (Temperature: 0.7 - conversational)
        │                   │
        └───────────────────┤
                            ▼
                         ┌─────┐
                         │ END │
                         └─────┘
```

### Retry Mechanism (Updated 2026-01-09)

**Before:** Validation errors caused workflow termination without retry.

**After:** Validation errors are stored in `query_result` and trigger the retry loop.

```
generate_SQL
    ↓
    LLM generates SQL
    ↓
validate_sql_query() (validation.py)
    ↓
┌─ PASS → execute_SQL → Success
│
└─ FAIL → Error stored in query_result + messages
              ↓
          execute_SQL (skips execution if error present)
              ↓
          check_query_validation (detects error in query_result)
              ↓
          ┌─ retry_count < 3 → generate_SQL (with error feedback)
          │
          └─ retry_count >= 3 → Return "Max retries exceeded" error
```

**Key Improvement:** `messages` array is updated with error to track retry count correctly, preventing infinite retry loops.

---

## Key Components

### 1. Intent Classification
- **Node:** `intent_classification`
- **LLM Temperature:** 0.0 (deterministic)
- **Purpose:** Routes between SQL generation and general conversation
- **Output:** `"sql"` or `"general"`

### 2. SQL Generation (Updated 2026-01-10)
- **Node:** `generate_SQL`
- **LLM Temperature:** 0.1 (accurate, low variance)
- **Prompt Selection:** Conditional based on `needs_pyodide` flag
  - **Simple SQL Prompt** (pyodide=True): Fetches raw data for Python analysis
    - No aggregations (AVG, SUM, COUNT)
    - No window functions (PARTITION BY, RANK)
    - No date functions (EXTRACT, TO_DATE, DATE_TRUNC)
    - Just SELECT columns AS-IS for Pandas processing
  - **Complex SQL Prompt** (pyodide=False): Full analytical queries
    - Aggregations, joins, subqueries allowed
    - Database performs all computation
- **Process:**
  1. Load schema from `schema_info.json` (cached)
  2. Check `needs_pyodide` flag from earlier classification
  3. Select appropriate prompt (simple vs complex)
  4. If retry: Add error-specific feedback from `feedbacks.py`
  5. Call LLM to generate SQL
  6. Parse XML response: `<reasoning>` + `<sql>`
  7. Validate SQL for security and correctness

### 3. SQL Validation (validation.py - Updated 2026-01-10)
- **Purpose:** Prevent SQL injection and ensure query correctness
- **Checks:**
  1. Forbidden keywords (DROP, DELETE, UPDATE, etc.)
  2. Multiple statements (semicolon check)
  3. Comments (-- or /* */)
  4. Unknown table names (with CTE/alias filtering)
- **Table Extraction Logic:**
  - Uses `sqlparse` to parse SQL into tokens
  - Skips `Function` and `Parenthesis` tokens to avoid false positives
  - **Bug Fix (2026-01-10):** Previously, `EXTRACT(DOW FROM "dateTime")` was incorrectly extracting "datetime" as a table name due to recursive processing of function tokens
  - **Solution:** Function/Parenthesis tokens are now skipped entirely without recursion
  - Only statement-level FROM/JOIN clauses are processed for table extraction
- **On Error:** Raises `SQLGenerationError` with detailed debug logs

### 4. Query Execution
- **Node:** `execute_SQL`
- **Process:**
  1. Skip execution if validation error already in `query_result`
  2. Execute SQL via SQLAlchemy
  3. Apply PII masking (deterministic, Python-based)
  4. Return JSON result or error message
- **Retry Limit:** 3 attempts (tracked via `messages` array)

### 5. Visualization Request Classification
- **Node:** `visualisation_request_classification`
- **LLM Temperature:** 0.0 (strict keyword detection)
- **Keywords:** "chart", "graph", "plot", "visualize", "visualization", "draw"
- **Default:** `"no"` (prevents over-generation)
- **Chart Types:** bar (comparison), line (time series), pie (proportions)

### 6. Pyodide Request Classification (Updated 2026-01-10)
- **Node:** `pyodide_request_classification`
- **Execution Order:** **BEFORE** SQL generation (prevents complex SQL when simple data fetch is needed)
- **Method:** Keyword-based detection
- **Keywords:**
  - `correlation`, `statistical analysis`, `statistics`
  - `standard deviation`, `variance`, `mean`
  - `distribution`, `skewness`, `kurtosis`
  - `outlier`, `outliers`, `percentile`, `quartile`
  - `time series`, `trend`, `seasonality`
  - `describe`, `summary`
- **Output:** `needs_pyodide` boolean (stored in state for later use)
- **Purpose:** Triggers simple SQL prompt to fetch raw data instead of performing analysis in database
- **Future Enhancement:** LLM-based classification with multilingual support

### 7. Chart Generation
- **Technology:** Plotly.js + react-plotly.js
- **Process:**
  1. Determine chart type from user question
  2. Extract x/y axes from SQL result columns
  3. Generate dynamic title from user question (60 char limit)
  4. Apply PII masking to data
  5. Return Plotly JSON spec to frontend

### 8. In-Browser Python Execution
- **Technology:** Pyodide (WebAssembly Python) + react-py
- **Libraries:** pandas (data manipulation)
- **Process:**
  1. LLM generates pandas analysis code
  2. Frontend loads Pyodide runtime
  3. Execute code in browser sandbox
  4. Display results in UI
- **Security:** No server-side code execution

### 9. Response Generation
- **Node:** `generate_response`
- **LLM Temperature:** 0.7 (natural, varied)
- **Output Format:** `<answer>` + `<insight>` (XML tags)
- **PII:** Already masked in data
- **Streaming:** Real-time response streaming to frontend

### 10. Error Feedback System (feedbacks.py) 🆕
- **Purpose:** Provide LLM-specific hints for error correction
- **Functions:**
  - `get_unknown_tables_feedback()` - Invalid table names
  - `get_multiple_statements_feedback()` - Semicolon usage
  - `get_sql_comments_feedback()` - Comment removal
  - `get_forbidden_keyword_feedback()` - Dangerous keywords
  - `get_column_not_found_feedback()` - Case sensitivity
- **Example:** "Your previous attempt used invalid table 'it'. Use ONLY: customers, orders, products..."

---

## Data Flow

### User Question → SQL Result

```
1. User Input
   "Show me top 5 customers by total spending"

2. Intent Classification (LLM)
   → intent: "sql"

3. SQL Generation (LLM + Schema)
   schema_info.json → Prompt
   → SQL: SELECT c."name", SUM(o."amount") as total FROM customers c JOIN orders o...

4. SQL Validation (validation.py)
   ✓ No dangerous keywords
   ✓ Single statement
   ✓ No comments
   ✓ Tables exist: customers, orders

5. Query Execution (PostgreSQL)
   → Result: [{"name": "Person #1", "total": 15000}, ...]
   → PII masked: "John Smith" → "Person #1"

6. Visualization Check (LLM)
   → visualise: "no" (no chart keywords in question)

7. Pyodide Check (Keyword)
   → needs_pyodide: false

8. Response Generation (LLM)
   → Answer: "The top 5 customers by total spending are..."
   → Insight: "Person #1 accounts for 30% of total revenue..."

9. Frontend Display
   → Streaming text response to user
```

### Error Retry Flow (Updated 2026-01-09)

```
1. SQL Generation Attempt #1
   → SQL: SELECT * FROM it WHERE ...

2. Validation Failed
   → Error: "Unknown tables in query: {'it'}"
   → Stored in query_result + messages (AIMessage)

3. execute_SQL (Skip)
   → Detects error in query_result → return {} (pass through)

4. check_query_validation
   → is_error_result(query_result) → True
   → retry_count = 1 (from messages)
   → return "retry"

5. SQL Generation Attempt #2 (with feedback)
   → Previous error: "Unknown tables: {'it'}"
   → Feedback: "Use ONLY: customers, orders, products. Do NOT abbreviate."
   → SQL: SELECT * FROM customers WHERE ...

6. Validation Passed
   → execute_SQL → Success
```

---

## Dataset-Agnostic Design

### Core Principle
**All table/column information is loaded from `schema_info.json` at runtime, not hardcoded in prompts.**

### Implementation

1. **Schema Generation** (generate_schema.py)
   - Reads database metadata
   - Detects PII columns via LLM
   - Outputs `schema_info.json`

2. **Runtime Loading** (nodes.py:95-120)
   ```python
   def load_schema_info() -> str:
       global _SCHEMA_CACHE
       if _SCHEMA_CACHE is None:
           with open(SCHEMA_JSON_PATH, 'r') as f:
               schema_data = json.load(f)
           _SCHEMA_CACHE = format_schema_for_prompt(schema_data)
       return _SCHEMA_CACHE
   ```

3. **Prompt Injection** (prompts.py:85-175)
   ```python
   def get_sql_generation_prompt(schema_info: str, user_question: str) -> str:
       return f"""
       <database_schema>
       {schema_info}
       </database_schema>

       <user_question>
       {user_question}
       </user_question>
       """
   ```

### Benefits
- ✅ Swap datasets by replacing CSVs and re-running pipeline
- ✅ No code changes required for new schemas
- ✅ Scalable to different domains (retail, healthcare, finance, etc.)

---

## Module Responsibilities

### agent/ - LangGraph Workflow
- **graph.py:** StateGraph definition, conditional edges, retry logic
- **nodes.py:** Node implementations, LLM calls, error handling
- **prompts.py:** LLM prompt templates (initial generation)
- **feedbacks.py:** Error feedback messages (retry corrections)
- **state.py:** TypedDict schema for state management

### core/ - Shared Utilities
- **validation.py:** SQL security checks, table name validation
- **db.py:** Database connection pooling (singleton pattern)
- **logger.py:** Structured logging configuration
- **errors.py:** Custom exception hierarchy
- **console.py:** CLI output formatting

### data_pipeline/ - ETL
- **profiler.py:** Analyze CSV structure and statistics
- **relationship_discovery.py:** Suggest FK relationships (interactive)
- **load_data.py:** CSV → PostgreSQL with constraints
- **integrity_checker.py:** Validate PK/FK integrity, detect offsets
- **transform_data.py:** Interactive SQL console for data fixes
- **pii_discovery.py:** LLM-based PII column detection
- **generate_schema.py:** Create schema metadata + PII report
- **setup.py:** Automated pipeline orchestration

---

## Performance Optimizations

### 1. Caching
- **Schema:** Loaded once, cached globally (`_SCHEMA_CACHE`)
- **Database Engine:** Connection pool reused (`_DB_ENGINE`)
- **Frontend:** Plotly chart memoized (React.memo)

### 2. Temperature Tuning
- **Intent (0.0):** Deterministic routing
- **SQL (0.1):** Accurate, minimal hallucination
- **Visualization (0.0):** Strict keyword matching
- **Response (0.7):** Natural, varied language

### 3. Streaming
- **LangGraph Server:** Real-time response streaming
- **Frontend:** Progressive UI updates

### 4. Connection Pooling
- **SQLAlchemy:** pool_size=5, max_overflow=10
- **Reuses connections** across requests

---

## Security Layers

### 1. SQL Injection Prevention (validation.py)
- Forbidden keyword blocking
- Multiple statement prevention
- Comment removal
- Table name whitelist validation

### 2. PII Masking (nodes.py:128-194)
- LLM-based detection during schema generation
- Deterministic masking at query execution
- Person names → "Person #N" (sequential)
- Organization names preserved

### 3. Read-Only Access
- Only SELECT queries allowed
- No write operations (INSERT, UPDATE, DELETE)
- No schema modifications (CREATE, ALTER, DROP)

### 4. Rate Limiting
- Max retry limit: 3 attempts
- Prevents infinite loops

---

## Technology Choices

### Why LangGraph?
- **State Management:** Built-in state persistence
- **Conditional Routing:** Easy error handling with conditional edges
- **Streaming:** Native streaming support
- **Debugging:** LangSmith integration for trace visualization

### Why Cerebras (llama-3.3-70b)?
- **Performance:** Fast inference (previously Groq)
- **OpenAI-compatible API:** Easy integration
- **Cost-effective:** Competitive pricing

### Why PostgreSQL?
- **Relational:** Strong FK constraint support
- **JSON Support:** Native JSON column types
- **Mature:** Well-documented, stable

### Why Next.js 15?
- **App Router:** Server components, streaming
- **React 19:** Latest features (concurrent rendering)
- **TypeScript:** Type safety

---

## Related Documentation

- [Error Handling Guide](ERROR-HANDLING.md) - SQL validation, retry logic, debugging
- [Development Guide](DEVELOPMENT.md) - Contributing and extending *(coming soon)*
- [SQL Reference](sql.md) - SQL patterns and examples
- README.md - User setup and usage

---

**Last Updated:** 2026-01-10
**Version:** 1.1
**Recent Changes:**
- Workflow restructured: Pyodide classification now runs BEFORE SQL generation
- Added simple SQL prompt for pyodide-based analysis (no aggregations/functions)
- Fixed validation.py to skip Function/Parenthesis tokens (prevents false table extraction)
