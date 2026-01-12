# Delivery Cadet

An AI-powered data exploration agent that answers natural language questions over structured databases using LangGraph and LLM technology.

## Overview

Delivery Cadet is an intelligent SQL agent that converts natural language questions into SQL queries, executes them against a PostgreSQL database, and returns results in a conversational format through a ChatGPT-style interface.

**Key capabilities include:**

- Natural language to SQL conversion with automatic retry
- Interactive data visualization (bar, line, pie, scatter, area charts)
- In-browser Python execution for advanced analytics
- Automated ETL pipeline with PII detection and masking
- Dataset-agnostic design for easy adaptation

> **📚 For detailed features, tech stack, and system architecture, see the [Architecture Guide](docs/ARCHITECTURE.md).**

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (for PostgreSQL database)
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **pnpm** (installed via npm)
- **Cerebras API key** (free tier at [Cerebras Cloud](https://cloud.cerebras.ai))
- **LangSmith API key** (optional, for tracing - free tier at [LangSmith](https://smith.langchain.com))

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/DachshundMango/delivery-cadet-challenge.git
cd cadet
```

### 2. Environment Variables

Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

```bash
# Cerebras API Key (Required)
CEREBRAS_API_KEY=your_cerebras_api_key_here

# LLM Model Configuration
LLM_MODEL=llama-3.3-70b

# LangSmith Settings (Required for trace visualisation)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=delivery-cadet-challenge

# Database Settings (Required)
DB_USER=myuser
DB_PASSWORD=mypassword
DB_NAME=delivery_db

# PgAdmin Settings (Optional)
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin
```

**Required API Keys:**

- **Cerebras API Key**: Get free tier at [https://cloud.cerebras.ai](https://cloud.cerebras.ai)
- **LangSmith API Key**: Get free tier at [https://smith.langchain.com](https://smith.langchain.com)

### 3. Install Python Dependencies

**Using pip with virtual environment (Recommended)**

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install all dependencies
pip install -r requirements.txt
```

> **Note:** The `requirements.txt` specifies core packages with pinned versions. Pip automatically installs all transitive dependencies (~150 additional packages) with compatible versions.

**Alternative: Using Conda**

If you prefer conda:

```bash
# Create conda environment with Python 3.12
conda create -n cadet python=3.12
conda activate cadet

# Install dependencies via pip
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
# Install pnpm if not already installed
npm install -g pnpm

cd frontend
pnpm install
cd ..
```

> **Note:** This project uses pnpm as specified in `package.json`. Using npm or yarn may cause dependency conflicts.

### 5. Configure Frontend Environment

Copy the frontend environment example file:

```bash
cp frontend/.env.example frontend/.env.local
```

The default values are suitable for local development. You only need to change them if:

- Your LangGraph server runs on a different port
- You've customized the agent ID in `langgraph.json`

### 6. Start PostgreSQL Database

```bash
# From root directory
docker-compose up -d
```

This will start:

- PostgreSQL on port 5432
- PgAdmin on port 8080 (http://localhost:8080)

## Database Setup

The easiest way to set up your database:

```bash
python src/setup.py
```

This runs an automated 6-step pipeline (profiler → relationship discovery → load data → integrity check → transform → schema generation with PII detection). The script is interactive and pauses for user input when needed.

For detailed pipeline documentation and manual setup, see the [Architecture Guide](docs/ARCHITECTURE.md#data-pipeline).

## Running the Application

### Quick Start

```bash
./start.sh
```

This automatically starts both LangGraph server (port 2024) and frontend (port 3000), then opens http://localhost:3000 in your browser. On first run, it will automatically set up the database.

**Reset and start fresh:**

```bash
./start.sh --reset
```

This drops all tables, clears config files, and re-runs the setup pipeline.

For manual setup, CLI mode, and development server options, see the [Development Guide](docs/DEVELOPMENT.md#running-the-application).

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
- **Permission denied (./start.sh)**: Run `chmod +x start.sh` first
- **Module not found errors**: Make sure you've installed all dependencies with `pip install -r requirements.txt`

For detailed troubleshooting, see the [Development Guide](docs/DEVELOPMENT.md#troubleshooting).

## Documentation

For detailed system documentation and developer guides, see the [docs/](docs/) folder:

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design, LangGraph workflow, project structure, and component details
- **[Error Handling Guide](docs/ERROR-HANDLING.md)** - SQL validation, error types, retry mechanism, and debugging
- **[Development Guide](docs/DEVELOPMENT.md)** - Development setup, contributing, testing, limitations, and roadmap

## License

This project is developed as part of the Delivery Cadet Challenge 2026.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- UI template based on [LangGraph Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui)
- Powered by [Cerebras](https://cerebras.ai/) for fast LLM inference
