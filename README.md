# Delivery Cadet

An AI-powered data exploration agent that answers natural language questions over structured databases using LangGraph and LLM technology.

## Overview

Delivery Cadet is an intelligent SQL agent that converts natural language questions into SQL queries, executes them against a PostgreSQL database, and returns results in a conversational format through a ChatGPT-style interface. The system is designed to be dataset-agnostic, allowing easy adaptation to different databases without major refactoring.

## Features

### Core Capabilities
- **Natural Language to SQL**: Converts user questions into valid PostgreSQL queries
- **Intent Classification**: Intelligently routes between SQL-based queries and general conversation
- **Automatic Query Retry**: Self-correcting mechanism for failed queries
- **Data Visualisation**: Automatic chart generation (bar, line, pie, scatter, area) using Plotly for visual data insights
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

- **Backend**: Python 3.x, LangGraph, Cerebras (llama-3.3-70b), PostgreSQL 15, SQLAlchemy, Plotly
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Pyodide (in-browser Python)
- **Infrastructure**: Docker Compose, LangGraph Server

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- pnpm (or npm/yarn)
- Cerebras API key (free tier available at [Cerebras Cloud](https://cloud.cerebras.ai))
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
# Cerebras API Key
CEREBRAS_API_KEY=your_cerebras_api_key_here

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

If you prefer to run each step individually, the data pipeline consists of:

1. **profiler** - Analyze CSV files → generates `data_profile.json`
2. **relationship_discovery** - Configure PK/FK relationships → generates `keys.json`
3. **load_data** - Load CSV data to PostgreSQL with constraints
4. **integrity_checker** - Validate data integrity (optional)
5. **transform_data** - Fix issues via interactive SQL console (if needed)
6. **generate_schema** - Generate schema metadata + PII detection → generates `schema_info.json`

For detailed workflow diagrams and explanations, see the [Architecture Guide](docs/ARCHITECTURE.md).

Run each command individually if you need more control:

```bash
# Step 1: Profile CSV files
python -m src.data_pipeline.profiler

# Step 2: Discover relationships
python -m src.data_pipeline.relationship_discovery

# Step 3: (Optional) Check data integrity
python -m src.data_pipeline.integrity_checker

# Step 4: Load data to PostgreSQL
python -m src.data_pipeline.load_data

# Step 5: (If needed) Fix issues via interactive SQL console
python -m src.data_pipeline.transform_data

# Step 6: Generate schema + detect PII
python -m src.data_pipeline.generate_schema
```

**Note**: Step 6 uses LLM to detect PII columns and displays a color-coded report for verification. Personal names are automatically masked as `Person #N` at runtime.

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

## Limitations & Future Improvements

### Current Limitations

1. **Limited Chart Types**: Currently supports bar, line, pie, scatter, and area charts
   - Heatmaps, box plots, histograms, and other advanced visualisations not yet implemented

2. **Pyodide Performance**: Python execution triggered by keyword matching
   - Simple keyword-based classification may miss nuanced analysis requests
   - Pandas loading time (~2-3 seconds) on first use
   - Increased browser memory consumption

3. **LLM-Based PII Detection**: Uses LLM to identify personal information columns
   - Accuracy depends on sample data quality and LLM reasoning
   - May miss PII columns with ambiguous names or unclear data patterns
   - Requires manual verification via color-coded report
   - Can be manually adjusted by editing `schema_info.json`

4. **Single LLM Dependency**: If Cerebras API is down, entire system fails
   - No fallback mechanism

5. **No Query Caching**: Identical queries are re-executed each time
   - Slower for repeated questions

### Planned Improvements

1. **Advanced Visualisations**: Expand chart types beyond current set
   - Heatmaps, box plots, histograms (scatter and area charts implemented)
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
./start.sh --reset
```

This will drop all database tables, delete config files, and re-run the entire pipeline.

### Common Issues

- **Schema not found**: Run `python src/setup.py`
- **Database connection error**: Check if PostgreSQL is running with `docker-compose ps`
- **Port conflict**: Edit `langgraph.json` to use a different port

For detailed troubleshooting, see the [Development Guide](docs/DEVELOPMENT.md#troubleshooting).

## Documentation

For detailed system documentation and developer guides, see the [docs/](docs/) folder:

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design, LangGraph workflow, project structure, and component details
- **[Error Handling Guide](docs/ERROR-HANDLING.md)** - SQL validation, error types, retry mechanism, and debugging
- **[Development Guide](docs/DEVELOPMENT.md)** - Development setup, contributing, testing, and common tasks

## License

This project is developed as part of the Delivery Cadet Challenge 2026.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- UI template based on [LangGraph Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui)
- Powered by [Cerebras](https://cerebras.ai/) for fast LLM inference
