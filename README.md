# Delivery Cadet

An AI-powered data exploration agent that answers natural language questions over structured databases using LangGraph and LLM technology.

## Overview

Delivery Cadet is an intelligent SQL agent that converts natural language questions into SQL queries, executes them against a PostgreSQL database, and returns results in a conversational format through a ChatGPT-style interface. The system is designed to be dataset-agnostic, allowing easy adaptation to different databases without major refactoring.

## Features

### Core Capabilities
- **Natural Language to SQL**: Converts user questions into valid PostgreSQL queries
- **Intent Classification**: Intelligently routes between SQL-based queries and general conversation
- **Automatic Query Retry**: Self-correcting mechanism for failed queries
- **Data Visualization**: Automatic chart generation (bar, line, pie) using Plotly for visual data insights
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
- **PII Masking**: Guardrail system to obscure personal names (currently disabled for testing)
- **Execution Tracing**: LangSmith integration for debugging and monitoring

## Tech Stack

### Backend
- **Python 3.x**: Core programming language
- **LangGraph**: State-based workflow orchestration
- **LangChain**: LLM framework and tooling
- **Groq**: High-performance LLM inference (llama-3.1-8b-instant)
- **PostgreSQL 15**: Primary database
- **SQLAlchemy**: Database ORM and query builder
- **Plotly**: Interactive data visualization library
- **FastAPI**: Web server (via LangGraph)
- **LangSmith**: Execution trace visualization

### Frontend
- **Next.js 15**: React meta-framework (App Router)
- **React 19**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS 4**: Styling
- **Radix UI**: Accessible component library
- **Plotly.js & React-Plotly.js**: Interactive charting library
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
git clone <repository-url>
cd cadet
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```bash
# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# LangSmith Settings (Required for trace visualization)
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

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
pnpm install
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

### Step 1: Profile the Data

```bash
python src/profiler.py
```

This generates `data_profile.json` with statistics about each CSV file.

### Step 2: (Optional) Discover Relationships

```bash
python src/relationship_discovery.py
```

This suggests potential foreign key relationships based on column names and data patterns.

### Step 3: Load Data into Database

```bash
python src/load_data.py
```

This script:
- Creates tables from CSV files
- Applies primary and foreign key constraints from `keys.json`
- Loads data into PostgreSQL
- Validates data integrity

### Step 4: Generate Schema Information

```bash
python src/generate_schema.py
```

This creates:
- `schema_info.json`: Structured schema metadata used by the LLM
- `schema_info.md`: Human-readable schema documentation

### Step 5: (Optional) Verify Data Integrity

```bash
python src/integrity_checker.py
```

Checks for:
- Primary key violations (duplicates, NULLs)
- Foreign key violations (orphaned records)

## Running the Application

### Option 1: Full Stack (Recommended)

**Terminal 1 - Start LangGraph Server:**
```bash
langgraph up
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

### Option 2: CLI Mode (Testing)

```bash
python src/cli.py
```

Interactive command-line interface for testing the agent directly.

## Project Structure

```
cadet/
├── src/                          # Python backend source code
│   ├── cli.py                    # CLI entry point
│   ├── graph.py                  # LangGraph workflow definition
│   ├── nodes.py                  # Agent node implementations
│   ├── state.py                  # State management schema
│   ├── load_data.py              # CSV to DB ETL pipeline
│   ├── generate_schema.py        # Schema metadata generator
│   ├── transform_data.py         # PK/FK synchronization
│   ├── integrity_checker.py      # Data validation utilities
│   ├── relationship_discovery.py # Automatic FK detection
│   ├── profiler.py               # CSV data profiler
│   ├── reset_db.py               # Database reset utility
│   ├── keys.json                 # PK/FK metadata configuration
│   └── schema_info.json          # Generated schema (used by LLM)
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
├── requirements.txt              # Python dependencies
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
4. **Visualization Request Classification**: Analyzes query results and determines if visual representation is needed
5. **Chart Generation**: Creates interactive Plotly charts (bar, line, pie) from SQL results
6. **Response Generation**: Converts SQL results into natural language
7. **Retry Logic**: Automatically regenerates queries on errors

### Dataset-Agnostic Design

The system loads schema information from `schema_info.json` at runtime, meaning:
- No hardcoded table or column names in prompts
- Easy to swap datasets by updating `keys.json` and re-running the data pipeline
- Schema metadata is automatically injected into LLM prompts

## Configuration

### Changing the Database

1. Place new CSV files in the `data/` directory
2. Edit `src/keys.json` to define primary and foreign keys:

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
python src/load_data.py
python src/generate_schema.py
```

### Changing the LLM Model

Edit `src/nodes.py` line 15:

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
- "Analyze daily sales trends over time."
- "Compare revenue by franchise size (S, M, L, XL, XXL) with average transaction values."

### Expert (Window Functions)
- "For each country, rank the products by total revenue and show only the top-selling product in each country."
- "Calculate the running cumulative revenue per day."
- "For each transaction, calculate how its total price compares to the average transaction value for that franchise."

## Technology Choices & Justification

### Why PostgreSQL?
- Robust support for complex joins and window functions
- Better performance for analytical queries than SQLite
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
- Server components for optimal performance
- Built-in API routes for proxy layer
- Excellent TypeScript support
- App Router provides modern React patterns

## Limitations & Future Improvements

### Current Limitations

1. **Limited Chart Types**: Currently supports only bar, line, and pie charts
   - Scatter plots, heatmaps, and other advanced visualizations not yet implemented

2. **No Python Execution**: Cannot perform advanced data analysis or transformations beyond SQL
   - Limited to SQL capabilities only

3. **Simple PII Masking**: Uses regex pattern matching for name detection
   - May not catch all PII or may over-mask legitimate data
   - Currently disabled for testing purposes

4. **Single LLM Dependency**: If Groq API is down, entire system fails
   - No fallback mechanism

5. **No Query Caching**: Identical queries are re-executed each time
   - Slower for repeated questions

### Planned Improvements

1. **Advanced Visualizations**: Expand chart types beyond bar, line, and pie
   - Scatter plots, heatmaps, box plots, histograms
   - Multi-axis and combination charts
   - Customizable chart styling and themes

2. **Pyodide Integration**: Enable in-browser Python execution
   - Allow pandas, numpy operations on query results
   - Enable advanced statistical analysis

3. **NER-based PII Detection**: Replace regex with named entity recognition
   - More accurate personal information detection
   - Reduced false positives

4. **LLM Fallback Chain**: Add OpenAI or Anthropic as backup
   - Graceful degradation if primary LLM fails

5. **Redis Caching Layer**: Cache SQL results and LLM responses
   - Faster responses for common questions
   - Reduced API costs

6. **Proactive Insights**: Agent automatically discovers interesting patterns
   - Periodic analysis of data
   - Suggested questions to users

7. **Multi-Database Support**: Extend beyond PostgreSQL
   - MySQL, SQLite, Snowflake adapters
   - Dialect-aware SQL generation

## Troubleshooting

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

**Solution**: Run `python src/generate_schema.py`

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

## License

This project is developed as part of the Delivery Cadet Challenge 2026.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- UI template based on [LangGraph Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui)
- Powered by [Groq](https://groq.com/) for fast LLM inference
