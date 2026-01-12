# System Architecture

This document provides a comprehensive overview of Delivery Cadet's system design, component structure, and data flow.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [High-Level Architecture](#high-level-architecture)
- [LangGraph Workflow](#langgraph-workflow)
- [Key Components](#key-components)
- [Data Flow](#data-flow)
- [Dataset-Agnostic Design](#dataset-agnostic-design)
- [Module Responsibilities](#module-responsibilities)

---

## Features

### Core Capabilities

- **Natural Language to SQL**: Converts user questions into valid PostgreSQL queries
- **Intent Classification**: Intelligently routes between SQL-based queries and general conversation
- **Automatic Query Retry**: Self-correcting mechanism for failed queries with LLM-powered error feedback
- **Data Visualisation**: Automatic chart generation (bar, line, pie, scatter, area) using Plotly for visual data insights
- **In-Browser Python Execution**: Pyodide-powered pandas analysis running directly in the browser for advanced statistical operations
- **Conversational Interface**: ChatGPT-style UI for seamless user interaction with streaming responses
- **Real-time Streaming**: Live response streaming through the web interface via LangGraph Server
- **Dataset-Agnostic Design**: Easily adaptable to new datasets via metadata configuration without code changes

### Data Pipeline

- **Automated ETL**: Robust CSV-to-database loading with automatic schema generation
- **Primary/Foreign Key Management**: Automatic key detection and relationship mapping with interactive configuration
- **Data Integrity Validation**: Built-in checks for referential integrity and constraint violations
- **Schema Profiling**: Automatic column analysis and statistics generation for optimal query planning
- **Relationship Discovery**: Intelligent FK relationship suggestions based on naming patterns and data analysis
- **Interactive Data Transformation**: SQL console for fixing data issues before loading

### Privacy & Security

- **LLM-Powered PII Detection**: Automatic identification of personal information columns during schema generation
- **Runtime PII Masking**: Personal names automatically replaced with `Person #1`, `Person #2`, etc. in query results
- **Human-in-the-Loop Verification**: Color-coded PII report for user review before masking activation
- **Manual Override**: Edit `schema_info.json` to add/remove PII columns as needed
- **SQL Injection Prevention**: Query validation blocks dangerous keywords (DROP, DELETE, UPDATE, etc.)
- **Read-Only Access**: Only SELECT queries allowed, no write operations
- **Execution Tracing**: LangSmith integration for debugging and monitoring

---

## Tech Stack

### Backend
- **Python 3.12**: Core application language
- **LangGraph**: State machine framework for agent workflow orchestration
- **Cerebras (llama-3.3-70b)**: Fast LLM inference for all AI tasks
- **PostgreSQL 15**: Relational database with JSON support
- **SQLAlchemy**: ORM and connection pooling
- **Plotly**: Interactive chart generation

### Frontend
- **Next.js 15**: React framework with App Router
- **React 19**: UI framework with concurrent rendering
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first styling
- **Pyodide**: In-browser Python runtime for pandas analysis
- **react-plotly.js**: Plotly charts in React

### Infrastructure
- **Docker Compose**: PostgreSQL and PgAdmin containerization
- **LangGraph Server**: Agent runtime with streaming support
- **LangSmith**: Execution tracing and debugging

---

## Project Structure

```
cadet/
├── src/                          # Python backend source code
│   ├── agent/                    # LangGraph agent workflow
│   │   ├── __init__.py           # Public API exports
│   │   ├── graph.py              # LangGraph workflow definition (76 LOC)
│   │   ├── nodes.py              # Agent node implementations (788 LOC)
│   │   ├── prompts/              # Modular LLM prompt templates (655 LOC)
│   │   │   ├── __init__.py       # Prompt exports
│   │   │   ├── intent.py         # Intent classification & general responses (68 LOC)
│   │   │   ├── sql.py            # SQL generation prompts (154 LOC)
│   │   │   ├── visualization.py  # Chart & visualization prompts (87 LOC)
│   │   │   ├── analysis.py       # Pyodide analysis prompts (63 LOC)
│   │   │   └── privacy.py        # PII masking & response prompts (245 LOC)
│   │   ├── helpers.py            # Reusable utilities (147 LOC)
│   │   ├── config.py             # LLM instances & constants (63 LOC)
│   │   ├── routing.py            # Conditional routing logic (106 LOC)
│   │   ├── feedbacks.py          # Error feedback messages (306 LOC)
│   │   ├── error_feedback.py     # Error feedback router (114 LOC)
│   │   └── state.py              # State management schema (65 LOC)
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
│   ├── DEVELOPMENT.md            # Development guide & contributing
│   └── ARCHITECTURE.md           # This file
│
├── tests/                        # Testing (672 LOC)
│   ├── test_security.py          # Security validation tests (111 LOC)
│   ├── agent/                    # Agent module tests
│   │   ├── test_routing.py       # Routing logic tests (143 LOC)
│   │   ├── test_helpers.py       # Helper utilities tests (185 LOC)
│   │   └── test_config.py        # Configuration tests (100 LOC)
│   └── README.md                 # Testing documentation
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
 [needs_pyodide=True]  [needs_pyodide=False]
      │            │
      └────┬───────┘
           ▼
      ┌───────────┐
      │generate_  │  Uses simple SQL (needs_pyodide=True)
      │   SQL     │  or complex SQL (needs_pyodide=False)
      └─────┬─────┘  (Temperature: 0.1 - accurate)
            │
            ▼
      ┌───────────┐
      │execute_SQL│
      └─────┬─────┘
            │
      ┌─────┴──────┐ (check_query_validation)
      │            │
  ┌───▼───┐    ┌───▼───────┐
  │[retry]│    │[fallback] │  sql_retry_count >= 3
  │       │    │           │  AND !pyodide_fallback_attempted
  └───┬───┘    └─────┬─────┘
      │              │
      │              ▼
      │        ┌─────────────────────┐
      │        │enable_pyodide_      │  Set needs_pyodide=True
      │        │    fallback         │  Reset sql_retry_count=0
      │        └──────────┬──────────┘  Clear query errors
      │                   │
      └───────────────────┘
                          │
                          ▼ (both retry paths lead back to generate_SQL)

      ┌──────────────────────────────┐
      │     [success]                │  No errors OR max retries exceeded
      └──────────┬───────────────────┘  with fallback already attempted
                 │
                 ▼
      ┌──────────────────────────────┐
      │visualisation_request_        │
      │      classification          │  Determine if chart is needed
      └───────────┬──────────────────┘  (Temperature: 0.0 - strict)
                  │
            ┌─────┴──────┐ (check_pyodide_classification)
            │            │
            ▼            ▼
   [needs_pyodide]   [skip]
            │            │
            ▼            │
   ┌─────────────────┐  │
   │generate_pyodide_│  │  Generate pandas analysis code
   │    analysis     │  │  (Injects CSV data)
   └────────┬────────┘  │
            │            │
            └────┬───────┘
                 ▼
            ┌───────────────┐
            │generate_      │
            │  response     │  Format natural language answer
            └───────┬───────┘  (Temperature: 0.7 - conversational)
                    │
                    ▼
                 ┌─────┐
                 │ END │
                 └─────┘
```

### Retry Mechanism

**Current Flow:**

```
generate_SQL
    ↓
    LLM generates SQL (simple if needs_pyodide=True, complex otherwise)
    ↓
validate_sql_query() (validation.py)
    ↓
┌─ PASS → execute_SQL → PostgreSQL execution
│           ↓
│       ┌─ Success → check_query_validation → "success" → visualisation
│       │
│       └─ SQL Error → query_result="Error: ..."
│                      sql_retry_count++
│                      ↓
│                  check_query_validation
│                      ↓
│                  ┌─ sql_retry_count < 3 → "retry" → generate_SQL (with feedback)
│                  │
│                  └─ sql_retry_count >= 3 (AND !pyodide_fallback_attempted)
│                                          → "fallback" → enable_pyodide_fallback
│                                                         ↓
│                                                     Set needs_pyodide=True
│                                                     Reset sql_retry_count=0
│                                                     Clear query_result
│                                                         ↓
│                                                     generate_SQL (simple SQL mode)
│
└─ FAIL → Error stored in query_result
          sql_retry_count++
          ↓
      execute_SQL (skips execution if error present)
          ↓
      check_query_validation (detects error in query_result)
          ↓
      ┌─ sql_retry_count < 3 → "retry" → generate_SQL (with error feedback)
      │
      └─ sql_retry_count >= 3 (AND !pyodide_fallback_attempted)
                              → "fallback" → enable_pyodide_fallback
```

**Key Features:**

1. **Dedicated Counter:** Uses `sql_retry_count` state variable to prevent token overflow
2. **Pyodide Fallback:** After 3 SQL failures, switches to simple SQL + Python analysis mode
3. **Fallback Guard:** `pyodide_fallback_attempted` flag prevents infinite fallback loops
4. **Targeted Feedback:** `error_feedback.py` provides specific hints based on error type

---

## Key Components

### 1. Intent Classification

- **Node:** `intent_classification`
- **LLM Temperature:** 0.0 (deterministic)
- **Purpose:** Routes between SQL generation and general conversation
- **Output:** `"sql"` or `"general"`

### 2. SQL Generation

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

### 3. SQL Validation (validation.py)

- **Purpose:** Prevent SQL injection and ensure query correctness
- **Checks:**
  1. Forbidden keywords (DROP, DELETE, UPDATE, etc.)
  2. Multiple statements (semicolon check)
  3. Comments (-- or /\* \*/)
  4. Unknown table names (with CTE/alias filtering)
- **Table Extraction Logic:**
  - Uses `sqlparse` to parse SQL into tokens
  - Skips `Function` and `Parenthesis` tokens to avoid false positives
  - **Implementation:** Function/Parenthesis tokens are skipped entirely without recursion to avoid extracting function arguments as table names
  - Only statement-level FROM/JOIN clauses are processed for table extraction
- **On Error:** Raises `SQLGenerationError` with detailed debug logs

### 4. Query Execution

- **Node:** `execute_SQL`
- **Process:**
  1. Skip execution if validation error already in `query_result`
  2. Execute SQL via SQLAlchemy
  3. Apply PII masking (deterministic, Python-based)
  4. Return JSON result or error message
- **Retry Limit:** 3 attempts (tracked via `sql_retry_count` in state)
- **Error Handling:**
  - Validation errors: Skips execution, passes error through
  - Database errors: Increments `sql_retry_count`, stores error in `query_result`

### 5. Visualization Request Classification

- **Node:** `visualisation_request_classification`
- **LLM Temperature:** 0.0 (strict keyword detection)
- **Keywords:** "chart", "graph", "plot", "visualize", "visualization", "draw"
- **Default:** `"no"` (prevents over-generation)
- **Chart Types:**
  - bar (comparison/ranking)
  - line (time series trends)
  - pie (proportions/breakdown)
  - scatter (correlation between two numeric variables)
  - area (time series with cumulative/fill emphasis)

### 6. Pyodide Request Classification

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
  2. Data injected as CSV format (not JSON) for efficiency
  3. Frontend loads Pyodide runtime
  4. Execute code in browser sandbox
  5. Display results in UI
- **Security:** No server-side code execution
- **Data Format:** CSV string injected directly into Python code to prevent JSON parsing overhead

### 9. Pyodide Fallback Mechanism

- **Node:** `enable_pyodide_fallback`
- **Trigger:** After 3 consecutive SQL generation/execution failures
- **Purpose:** Recover from complex SQL errors by simplifying the query strategy
- **Process:**
  1. Set `needs_pyodide=True` to enable simple SQL mode
  2. Reset `sql_retry_count=0` for fresh retry attempts
  3. Clear `query_result` and `sql_query` error states
  4. Set `pyodide_fallback_attempted=True` to prevent infinite loops
  5. Route back to `generate_SQL` with simplified prompt
- **Fallback Strategy:**
  - **Before fallback:** Complex SQL with aggregations, window functions, date operations
  - **After fallback:** Simple SELECT to fetch raw data, analysis delegated to Pyodide (pandas)
- **Guard Mechanism:** If fallback also fails after 3 attempts, routes to `generate_response` with error message

### 10. Response Generation

- **Node:** `generate_response`
- **LLM Temperature:** 0.7 (natural, varied)
- **Output Format:** `<answer>` + `<insight>` (XML tags)
- **PII:** Already masked in data
- **Streaming:** Real-time response streaming to frontend

### 11. Error Feedback System

- **Architecture:** Two-layer system for targeted error correction
  - **feedbacks.py (306 LOC):** Message templates for each error type
  - **error_feedback.py (114 LOC):** Router that analyzes errors and selects appropriate feedback
- **Purpose:** Provide LLM-specific hints for error correction during retry attempts
- **Process:**
  1. `nodes.py` calls `get_sql_error_feedback(error_message, allowed_tables)`
  2. `error_feedback.py` analyzes error message (regex matching)
  3. Routes to appropriate feedback generator in `feedbacks.py`
  4. Returns targeted hint string to append to SQL generation prompt
- **Feedback Types (feedbacks.py):**
  - `get_unknown_tables_feedback()` - Invalid table names (with alias detection)
  - `get_multiple_statements_feedback()` - Semicolon usage (suggest CTE)
  - `get_sql_comments_feedback()` - Comment removal
  - `get_forbidden_keyword_feedback()` - Dangerous keywords (CREATE, DROP, etc.)
  - `get_column_not_found_feedback()` - Case sensitivity and quoting rules
  - `get_division_by_zero_feedback()` - NULLIF usage
  - `get_datetime_format_feedback()` - Direct casting instead of TO_TIMESTAMP
  - `get_alias_reference_feedback()` - Alias in same SELECT clause (suggest CTE)
  - `get_parsing_error_feedback()` - Generic syntax errors (catch-all)
- **Example:** "Your previous attempt used invalid table 'it'. Use ONLY: customers, orders, products..."
- **Separation of Concerns:**
  - **feedbacks.py** stores human-readable messages (easy to modify/translate)
  - **error_feedback.py** handles error analysis logic (pattern matching)

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

### Error Retry Flow

```
1. SQL Generation Attempt #1
   → SQL: SELECT * FROM it WHERE ...

2. Validation Failed
   → Error: "Unknown tables in query: {'it'}"
   → Stored in query_result
   → sql_retry_count = 1

3. execute_SQL (Skip)
   → Detects error in query_result → return {} (pass through)

4. check_query_validation
   → is_error_result(query_result) → True
   → sql_retry_count = 1 < 3
   → return "retry"

5. SQL Generation Attempt #2 (with feedback)
   → Previous error: "Unknown tables: {'it'}"
   → Feedback: "Use ONLY: customers, orders, products. Do NOT abbreviate."
   → SQL: SELECT * FROM customers WHERE ...

6. Validation Passed
   → execute_SQL → Success
```

### Pyodide Fallback Flow

```
1. SQL Generation Attempts #1, #2, #3
   → All failed with complex SQL errors (e.g., date function issues)
   → sql_retry_count = 3

2. check_query_validation
   → sql_retry_count >= 3
   → pyodide_fallback_attempted = False
   → return "fallback"

3. enable_pyodide_fallback
   → Set needs_pyodide = True
   → Reset sql_retry_count = 0
   → Clear query_result = None
   → Set pyodide_fallback_attempted = True

4. SQL Generation Attempt #4 (Simple SQL Mode)
   → Uses get_simple_sql_for_pyodide_prompt()
   → SQL: SELECT "column1", "column2", "dateTime" FROM table
   → No aggregations, no window functions, no date operations

5. execute_SQL → Success
   → Raw data fetched: [{"column1": "value", "dateTime": "2024-01-01"}, ...]

6. visualisation_request_classification
   → check_pyodide_classification
   → needs_pyodide = True → route to generate_pyodide_analysis

7. generate_pyodide_analysis
   → Generates pandas code for statistical analysis
   → Injects CSV data directly into code
   → Returns ToolMessage with Python code

8. generate_response
   → Formats final answer with analysis results
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

- **graph.py:** StateGraph definition, conditional edges, retry logic, Pyodide fallback routing
- **nodes.py:** Node implementations, LLM calls, error handling, PII masking
- **prompts/:** Modular LLM prompt templates organized by function
  - **intent.py:** Intent classification & general conversation responses
  - **sql.py:** SQL generation prompts (complex & simple modes for Pyodide)
  - **visualization.py:** Chart request detection & title generation
  - **analysis.py:** Pyodide analysis code generation prompts
  - **privacy.py:** PII masking & natural language response formatting
- **helpers.py:** Reusable utilities (schema caching, DB engine pooling, PII masking)
- **config.py:** LLM instances with task-specific temperatures & workflow constants
- **routing.py:** Conditional routing logic (RouteDecider class with static methods)
- **feedbacks.py:** Error feedback messages - actual feedback strings for each error type
- **error_feedback.py:** Error feedback router - analyzes errors and routes to appropriate feedback
- **state.py:** TypedDict schema for state management (includes fallback flags and retry counters)

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
- **Frontend:** Chart stability via revision prop and explicit sizing

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
- [Development Guide](DEVELOPMENT.md) - Contributing and extending
- README.md - User setup and usage

---

**Last Updated:** 2026-01-11
