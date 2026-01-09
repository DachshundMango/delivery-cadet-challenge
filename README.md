# Delivery Cadet

An AI-powered data exploration agent that answers natural language questions over structured databases using LangGraph and LLM technology.

## Overview

Delivery Cadet is an intelligent SQL agent that converts natural language questions into SQL queries, executes them against a PostgreSQL database, and returns results in a conversational format through a ChatGPT-style interface. The system is designed to be dataset-agnostic, allowing easy adaptation to different databases without major refactoring.

## Features

### Core Capabilities
- **Natural Language to SQL**: Converts user questions into valid PostgreSQL queries
- **Intent Classification**: Intelligently routes between SQL-based queries and general conversation
- **Automatic Query Retry**: Self-correcting mechanism for failed queries
- **Data Visualisation**: Automatic chart generation (bar, line, pie) using Plotly for visual data insights
- **In-Browser Python Execution**: Pyodide-powered pandas analysis running directly in the browser
- **Conversational Interface**: ChatGPT-style UI for seamless user interaction
- **Real-time Streaming**: Live response streaming through the web interface
- **Dataset-Agnostic Design**: Easily adaptable to new datasets via metadata configuration

### Data Pipeline
- **Automated ETL**: Robust CSV-to-database loading with automatic schema generation
- **Primary/Foreign Key Management**: Automatic key detection and relationship mapping
- **Data Integrity Validation**: Built-in checks for referential integrity and constraint violations
- **Schema Profiling**: Automatic column analysis and statistics generation
- **Relationship Discovery**: Intelligent FK relationship suggestions based on naming patterns

### Privacy & Security
- **LLM-Powered PII Detection**: Automatic identification of personal information columns during schema generation
- **Runtime PII Masking**: Personal names automatically replaced with `Person #1`, `Person #2`, etc. in query results
- **Human-in-the-Loop Verification**: Color-coded PII report for user review before masking activation
- **Manual Override**: Edit `schema_info.json` to add/remove PII columns as needed
- **SQL Injection Prevention**: Query validation blocks dangerous keywords (DROP, DELETE, UPDATE, etc.)
- **Execution Tracing**: LangSmith integration for debugging and monitoring

## Tech Stack

### Backend
- **Python 3.x**: Core programming language
- **LangGraph**: State-based workflow orchestration
- **LangChain**: LLM framework and tooling
- **Groq**: High-performance LLM inference (llama-3.1-8b-instant)
- **PostgreSQL 15**: Primary database
- **SQLAlchemy**: Database ORM and query builder
- **Plotly**: Interactive data visualisation library
- **FastAPI**: Web server (via LangGraph)
- **LangSmith**: Execution trace visualisation

### Frontend
- **Next.js 15**: React meta-framework (App Router)
- **React 19**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS 4**: Styling
- **Radix UI**: Accessible component library
- **Plotly.js & React-Plotly.js**: Interactive charting library
- **Pyodide & react-py**: In-browser Python runtime with pandas support
- **Framer Motion**: Animations

### Infrastructure
- **Docker Compose**: PostgreSQL and PgAdmin containers
- **LangGraph Server**: Agent runtime environment

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- pnpm (or npm/yarn)
- Groq API key (free tier available at [GroqCloud](https://console.groq.com))
- LangSmith API key (free tier available at [LangSmith](https://smith.langchain.com))

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/DachshundMango/delivery-cadet-challenge.git
cd cadet
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```bash
# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# LangSmith Settings (Required for trace visualisation)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=delivery-cadet-challenge

# Database Settings
DB_USER=myuser
DB_PASSWORD=mypassword
DB_NAME=delivery_db

# PgAdmin Settings
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin
```

### 3. Install Python Dependencies

**Option A: Using Conda (Recommended)**
```bash
# Create conda environment from environment.yml
conda env create -f environment.yml

# Activate the environment
conda activate cadet
```

**Option B: Using pip**
```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
pnpm install
cd ..
```

### 5. Start PostgreSQL Database

```bash
# From root directory
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- PgAdmin on port 8080 (http://localhost:8080)

## Database Setup

### Quick Start (Automated)

The easiest way to set up your database is using the automated pipeline:

```bash
# Activate conda environment
conda activate cadet

# Run automated setup (interactive)
python src/setup.py
```

This will automatically run all 6 pipeline steps:
1. **profiler** - Analyze CSV files
2. **relationship_discovery** - Configure PK/FK (interactive)
3. **load_data** - Load to PostgreSQL (may fail initially)
4. **integrity_checker** - Check data integrity
5. **transform_data** - Fix issues (interactive SQL console)
6. **generate_schema** - Generate schema + PII detection

The script pauses for user input when needed and provides clear progress updates.

### Manual Setup (Step-by-Step)

If you prefer to run each step individually:

### Data Pipeline Workflow

```
┌─────────────────┐
│   CSV Files     │  Raw data in data/ directory
│   (data/*.csv)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  1. profiler.py     │  Analyze CSV structure and statistics
└──────────┬──────────┘
           │
           │ Generates data_profile.json
           ▼
┌──────────────────────────────┐
│ 2. relationship_discovery.py │  Suggest PK/FK relationships
└───────────┬──────────────────┘
            │
            │ Generates keys.json (inferred)
            ▼
┌───────────────────────────┐
│ 3. integrity_checker.py   │  Validate data integrity (optional)
└────────────┬──────────────┘
             │
             │ Reports FK violations, PK duplicates
             ▼
┌─────────────────┐
│ 4. load_data.py │  Load CSV → PostgreSQL
└────────┬────────┘
         │
         │ Creates tables + applies constraints
         ▼
┌──────────────────────┐
│ 5. transform_data.py │  Fix integrity issues (if needed)
└──────────┬───────────┘
           │
           │ Interactive SQL console
           │ Updates keys.json from DB
           │ Verifies FK relationships
           ▼
┌─────────────────────────┐
│ 6. generate_schema.py   │  Generate schema metadata + PII detection
└──────────┬──────────────┘
           │
           │ Generates:
           │  - schema_info.json (for LLM)
           │  - schema_info.md (docs)
           │  - PII column mapping
           ▼
┌──────────────────┐
│  SQL Agent Ready │  System ready to accept queries
└──────────────────┘
```

### Step 1: Profile the Data

```bash
python -m src.data_pipeline.profiler
```

This generates `src/config/data_profile.json` with statistics about each CSV file.

### Step 2: Discover Relationships

```bash
python -m src.data_pipeline.relationship_discovery
```

This suggests potential foreign key relationships based on column names and data patterns, generating `src/config/keys.json`.

### Step 3: (Optional) Check Data Integrity

```bash
python -m src.data_pipeline.integrity_checker
```

Validates data **before** loading to database:
- Primary key violations (duplicates, NULLs)
- Foreign key violations (orphaned records)
- Systematic offset detection (e.g., ID mismatches across tables)

### Step 4: Load Data into Database

```bash
python -m src.data_pipeline.load_data
```

This script:
- Creates tables from CSV files
- Applies primary and foreign key constraints from `src/config/keys.json`
- Loads data into PostgreSQL

### Step 5: Transform Data (If Needed)

```bash
python -m src.data_pipeline.transform_data
```

**Interactive SQL console** for fixing integrity issues:

```sql
SQL> UPDATE "orders" SET "customerId" = "customerId" - 1000000;
Query executed: 1500 rows affected
SQL> UPDATE "reviews" SET "franchiseId" = "franchiseId" - 1000000;
Query executed: 800 rows affected
SQL> done
```

After typing `done`, the script automatically:
1. Updates `keys.json` from actual database constraints
2. Verifies all FK relationships
3. Reports any remaining integrity issues

### Step 6: Generate Schema + Detect PII

```bash
python -m src.data_pipeline.generate_schema
```

This script:
1. Generates schema metadata from database
2. **Uses LLM to detect PII columns** (e.g., customer names, reviewer names)
3. Displays color-coded report for user verification:
   - 🔴 `[PII]` - Personal information (will be masked)
   - 🟢 `[SAFE]` - Non-sensitive data
4. Saves configuration to `src/config/schema_info.json`

**Creates:**
- `src/config/schema_info.json`: Complete schema + PII column mapping (used by SQL Agent)
- `src/config/schema_info.md`: Human-readable documentation

**PII Masking**: Personal names are automatically replaced with `Person #1`, `Person #2`, etc. at runtime to protect privacy.

## Running the Application

### Option 1: One-Command Start (Easiest)

```bash
# Activate conda environment
conda activate cadet

# Start everything
./start.sh
```

This script will:
1. Check if `schema_info.json` exists
2. If not, automatically run `python src/setup.py` (first-time setup)
3. Start LangGraph server (port 2024)
4. Start frontend (port 3000)
5. Automatically open http://localhost:3000 in your browser

**Reset and start fresh:**
```bash
./start.sh --reset
```
This will:
- Delete all database tables
- Remove all config files (keys.json, schema_info.json, etc.)
- Run setup.py again
- Start servers

### Option 2: Manual Start (Full Stack)

**Terminal 1 - Start LangGraph Server:**
```bash
langgraph dev
```
Server runs on http://localhost:2024

**Terminal 2 - Start Frontend:**
```bash
cd frontend
pnpm dev
```
Frontend runs on http://localhost:3000

**Access the Application:**
Open http://localhost:3000 in your browser.

### Option 3: CLI Mode (Testing)

```bash
python3 src/cli.py
```

Interactive command-line interface for testing the agent directly.

## Project Structure

```
cadet/
├── src/                          # Python backend source code
│   ├── agent/                    # LangGraph agent workflow
│   │   ├── __init__.py           # Public API exports
│   │   ├── graph.py              # LangGraph workflow definition
│   │   ├── nodes.py              # Agent node implementations
│   │   └── state.py              # State management schema
│   │
│   ├── data_pipeline/            # ETL and data preparation
│   │   ├── __init__.py           # Public API exports
│   │   ├── profiler.py           # CSV data profiler
│   │   ├── relationship_discovery.py  # Automatic FK detection
│   │   ├── integrity_checker.py  # Data validation utilities
│   │   ├── load_data.py          # CSV to DB ETL pipeline
│   │   ├── transform_data.py     # Interactive data transformation
│   │   ├── pii_discovery.py      # LLM-based PII column detection
│   │   └── generate_schema.py    # Schema + PII metadata generator
│   │
│   ├── core/                     # Shared utilities
│   │   ├── __init__.py           # Public API exports
│   │   ├── console.py            # Unified CLI output formatting
│   │   ├── db.py                 # Database connection management
│   │   ├── logger.py             # Logging configuration
│   │   ├── errors.py             # Custom exception classes
│   │   └── validation.py         # Input validation utilities
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
├── frontend/                     # Next.js frontend
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   ├── components/           # React components
│   │   ├── providers/            # Context providers & LangGraph client
│   │   └── hooks/                # Custom React hooks
│   ├── package.json
│   └── tailwind.config.js
│
├── data/                         # CSV data files
│   ├── sales_customers.csv
│   ├── sales_franchises.csv
│   ├── sales_suppliers.csv
│   ├── sales_transactions.csv
│   ├── media_customer_reviews.csv
│   └── media_gold_reviews_chunked.csv
│
├── docker-compose.yaml           # PostgreSQL + PgAdmin
├── langgraph.json                # LangGraph configuration
├── start.sh                      # One-command startup script
├── environment.yml               # Conda environment (cross-platform)
├── requirements.txt              # Python dependencies (pip)
├── .env                          # Environment variables (create this)
└── README.md                     # This file
```

## How It Works

### LangGraph Workflow

```
┌─────────────┐
│    START    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ read_question   │  Extract user question
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ intent_classification│  Classify as "sql" or "general"
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌───────────┐  ┌─────────────────────────┐
│generate_  │  │generate_general_response│
│   SQL     │  └───────────┬─────────────┘
└─────┬─────┘              │
      │                    │
      ▼                    ▼
┌───────────┐           ┌─────┐
│execute_SQL│           │ END │
└─────┬─────┘           └─────┘
      │
  ┌───┴───┐
  │ Error?│
  └───┬───┘
      │
  ┌───┴───────┐
  │           │
  ▼           ▼
[retry]   [success]
  │           │
  │           ▼
  │     ┌──────────────────────────────┐
  │     │visualisation_request_        │
  │     │      classification          │  Determine if chart needed
  │     └───────────┬──────────────────┘
  │                 │
  │                 ▼
  │     ┌──────────────────────────────┐
  │     │pyodide_request_              │
  │     │      classification          │  Check if Python analysis needed
  │     └───────────┬──────────────────┘
  │                 │
  │           ┌─────┴──────┐
  │           │            │
  │           ▼            ▼
  │    [needs_pyodide] [skip]
  │           │            │
  │           ▼            │
  │  ┌─────────────────┐  │
  │  │generate_pyodide_│  │
  │  │    analysis     │  │
  │  └────────┬────────┘  │
  │           │            │
  │           └────┬───────┘
  │                ▼
  │           ┌───────────────┐
  │           │generate_      │
  │           │  response     │
  │           └───────┬───────┘
  │                   │
  └───────────────────┤
                      ▼
                   ┌─────┐
                   │ END │
                   └─────┘
```

### Key Components

1. **Intent Classification**: Determines if the user wants data (SQL) or conversation (general)
2. **SQL Generation**: Uses LLM to convert natural language to PostgreSQL queries
3. **Query Execution**: Runs SQL against the database and handles errors
4. **Visualisation Request Classification**: Analyses query results and determines if visual representation is needed
5. **Chart Generation**: Creates interactive Plotly charts (bar, line, pie) from SQL results
6. **Pyodide Request Classification**: Checks user question for analysis keywords (correlation, statistics, describe, etc.)
7. **Conditional Pyodide Execution**: Only generates Python code when advanced analysis is explicitly requested
8. **In-Browser Python Execution**: Executes pandas-based Python code using Pyodide in the browser
9. **Response Generation**: Converts SQL results into natural language
10. **Retry Logic**: Automatically regenerates queries on errors

### Dataset-Agnostic Design

The system loads schema information from `schema_info.json` at runtime, meaning:
- No hardcoded table or column names in prompts
- Easy to swap datasets by updating `keys.json` and re-running the data pipeline
- Schema metadata is automatically injected into LLM prompts

## Configuration

### Changing the Database

1. Place new CSV files in the `data/` directory
2. Edit `src/config/keys.json` to define primary and foreign keys:

```json
{
  "table_name": {
    "pk": "primary_key_column",
    "fks": [
      {
        "col": "foreign_key_column",
        "ref_table": "referenced_table",
        "ref_col": "referenced_column"
      }
    ]
  }
}
```

3. Run the data pipeline:
```bash
python -m src.data_pipeline.load_data
python -m src.data_pipeline.generate_schema
```

### Changing the LLM Model

Edit `src/agent/nodes.py` line 31:

```python
# Current: llama-3.1-8b-instant
llm = ChatGroq(model='llama-3.1-8b-instant')

# Alternative: llama-3.3-70b-versatile
# llm = ChatGroq(model='llama-3.3-70b-versatile')
```

## Example Queries

### Easy (Single Table)
- "What are the top 3 most popular products by total quantity sold?"
- "How many customers are there in each continent?"
- "What payment methods are used and how often?"

### Medium (Two-Table Joins)
- "Which country generates the highest total revenue?"
- "Who are the top 5 customers by total spending?"
- "Which franchises have received the most customer reviews?"

### Hard (Multi-Table Joins)
- "Show total revenue by supplier ingredient. Which ingredients are associated with the highest-selling franchises?"
- "Analyse daily sales trends over time."
- "Compare revenue by franchise size (S, M, L, XL, XXL) with average transaction values."

### Expert (Window Functions)
- "For each country, rank the products by total revenue and show only the top-selling product in each country."
- "Calculate the running cumulative revenue per day."
- "For each transaction, calculate how its total price compares to the average transaction value for that franchise."

## Technology Choices & Justification

### Why PostgreSQL?
- Robust support for complex joins and window functions
- Better performance for analytic queries than SQLite
- Production-ready with ACID compliance
- Docker makes setup trivial

### Why Groq?
- Extremely fast inference speed (important for real-time chat)
- Free tier with generous limits
- Excellent SQL generation capabilities with llama-3.1-8b-instant

### Why LangGraph?
- State-based workflow management ideal for multi-step agents
- Built-in support for conditional edges (intent routing, retry logic)
- Native LangSmith integration for debugging
- Production-ready with streaming support

### Why Next.js?
- Server components for optimised performance
- Built-in API routes for proxy layer
- Excellent TypeScript support
- App Router provides modern React patterns

## Limitations & Future Improvements

### Current Limitations

1. **Limited Chart Types**: Currently supports only bar, line, and pie charts
   - Scatter plots, heatmaps, and other advanced visualisations not yet implemented

2. **Pyodide Performance**: Python execution triggered by keyword matching
   - Simple keyword-based classification may miss nuanced analysis requests
   - Pandas loading time (~2-3 seconds) on first use
   - Increased browser memory consumption

3. **LLM-Based PII Detection**: Uses LLM to identify personal information columns
   - Accuracy depends on sample data quality and LLM reasoning
   - May miss PII columns with ambiguous names or unclear data patterns
   - Requires manual verification via color-coded report
   - Can be manually adjusted by editing `schema_info.json`

4. **Single LLM Dependency**: If Groq API is down, entire system fails
   - No fallback mechanism

5. **No Query Caching**: Identical queries are re-executed each time
   - Slower for repeated questions

### Planned Improvements

1. **Advanced Visualisations**: Expand chart types beyond bar, line, and pie
   - Scatter plots, heatmaps, box plots, histograms
   - Multi-axis and combination charts
   - Customisable chart styling and themes

2. **Smart Pyodide Triggering**: Enhance Python execution classification
   - Use LLM-based classification instead of keyword matching for better accuracy
   - Add support for Korean and other language keywords
   - Fine-tune trigger conditions to reduce false positives

3. **Extended Python Capabilities**: Add numpy, scipy, matplotlib support
   - Statistical hypothesis testing
   - Advanced mathematical operations
   - Chart generation from Python code

4. **Enhanced PII Detection**: Improve LLM-based detection accuracy
   - Fine-tune prompts for better edge case handling
   - Add support for additional PII types (emails, phone numbers, addresses)
   - Implement confidence scores for detection results

5. **LLM Fallback Chain**: Add OpenAI or Anthropic as backup
   - Graceful degradation if primary LLM fails

6. **Redis Caching Layer**: Cache SQL results and LLM responses
   - Faster responses for common questions
   - Reduced API costs

7. **Proactive Insights**: Agent automatically discovers interesting patterns
   - Periodic analysis of data
   - Suggested questions to users

8. **Multi-Database Support**: Extend beyond PostgreSQL
   - MySQL, SQLite, Snowflake adapters
   - Dialect-aware SQL generation

## Troubleshooting

### Reset Everything

If you want to start completely fresh:

```bash
# Option 1: Using start.sh
./start.sh --reset

# Option 2: Manual reset
python src/reset_db.py
python src/setup.py
```

This will:
- Drop all database tables
- Delete all config files (keys.json, schema_info.json, data_profile.json)
- Re-run the entire pipeline

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart db

# View logs
docker-compose logs db
```

### Schema Not Found Error

```
FileNotFoundError: schema_info.json not found
```

**Solution**: Run the automated setup:
```bash
python src/setup.py
```

Or run generate_schema manually:
```bash
python -m src.data_pipeline.generate_schema
```

### LangGraph Server Port Conflict

If port 2024 is already in use:

Edit `langgraph.json` or run:
```bash
langgraph up --port 8000
```

Then update frontend `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Frontend Connection Issues

Check that `frontend/.env.local` exists with:
```
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
```

## Documentation

For developers and contributors:

- **[Error Handling Guide](docs/ERROR-HANDLING.md)** - SQL validation, error types, retry mechanism, and debugging
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design, LangGraph workflow, and component details
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup, contributing, testing, and common tasks
- **[SQL Reference](docs/sql.md)** - SQL patterns and examples

## License

This project is developed as part of the Delivery Cadet Challenge 2026.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- UI template based on [LangGraph Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui)
- Powered by [Groq](https://groq.com/) for fast LLM inference
