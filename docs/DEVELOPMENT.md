# Development Guide

This guide helps developers contribute to Delivery Cadet, understand the codebase structure, and extend functionality.

## Table of Contents
- [Development Setup](#development-setup)
- [Code Structure](#code-structure)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Code Style](#code-style)
- [Common Tasks](#common-tasks)
- [Debugging](#debugging)

---

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL knowledge
- Git

### Initial Setup

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd cadet
conda env create -f environment.yml
conda activate cadet
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
cd frontend && pnpm install
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Start database:**
```bash
docker-compose up -d
```

5. **Load data:**
```bash
python -m src.data_pipeline.setup
```

6. **Run development servers:**
```bash
# Terminal 1: LangGraph server
langgraph dev

# Terminal 2: Frontend
cd frontend && pnpm dev
```

### Development Workflow

```
1. Create feature branch
2. Make changes
3. Run tests (pytest)
4. Test locally (manual)
5. Commit with clear message
6. Push and create PR
```

---

## Code Structure

### Module Organization

```
src/
├── agent/          # LangGraph workflow (state machine logic)
├── core/           # Shared utilities (validation, logging, DB)
├── data_pipeline/  # ETL and schema generation
└── config/         # Runtime configuration files
```

### Key Files

| File | Purpose | When to Modify |
|------|---------|---------------|
| `agent/graph.py` | Workflow structure | Adding new nodes or edges |
| `agent/nodes.py` | Node implementations | Changing node logic |
| `agent/prompts/` | LLM prompts | Improving SQL generation |
| `agent/helpers.py` | Utility functions | Caching or PII logic |
| `agent/config.py` | LLM configuration | Temperature tuning |
| `agent/routing.py` | Conditional routing | Modifying edge logic |
| `agent/feedbacks.py` | Error feedbacks | Enhancing error messages |
| `core/validation.py` | SQL security | Adding validation rules |
| `data_pipeline/generate_schema.py` | Schema generation | Changing schema format |

---

## Adding New Features

### Adding a New Node

1. **Define node function** in `agent/nodes.py`:
```python
def my_new_node(state: SQLAgentState) -> dict:
    """
    Description of what this node does.

    Args:
        state: Current workflow state

    Returns:
        Dictionary with state updates
    """
    user_question = state.get('user_question')

    # Your logic here
    result = process_something(user_question)

    return {
        "my_new_field": result
    }
```

2. **Update state schema** in `agent/state.py`:
```python
class SQLAgentState(TypedDict):
    # Existing fields...
    my_new_field: str  # Add new field
```

3. **Add node to graph** in `agent/graph.py`:
```python
# Add node
workflow.add_node("my_new_node", my_new_node)

# Add edge
workflow.add_edge("previous_node", "my_new_node")
workflow.add_edge("my_new_node", "next_node")
```

4. **Test the workflow:**
```bash
langgraph dev
# Test via frontend or CLI
```

### Adding Error Feedback

1. **Create feedback function** in `agent/feedbacks.py`:
```python
def get_my_error_feedback(error_details: str) -> str:
    """
    Generate feedback for my custom error.

    Args:
        error_details: Details of the error

    Returns:
        Formatted feedback string
    """
    return f"""

**CRITICAL FIX REQUIRED:**
Your previous attempt had {error_details}.

How to fix:
1. Step one
2. Step two
"""
```

2. **Use in nodes.py:**
```python
from src.agent.feedbacks import get_my_error_feedback

if 'My Error Type' in previous_error:
    sql_prompt += get_my_error_feedback(error_details)
```

### Adding Validation Rule

1. **Extend validation** in `core/validation.py`:
```python
def validate_sql_query(sql_query: str, allowed_tables: Set[str]) -> bool:
    # Existing validations...

    # Add new validation
    if my_custom_check(sql_query):
        raise SQLGenerationError(
            "My custom error message",
            details={'query': sql_query}
        )
```

2. **Add corresponding feedback** in `feedbacks.py`:
```python
def get_my_validation_error_feedback() -> str:
    return "How to fix this validation error..."
```

3. **Update error handling** in `nodes.py`:
```python
elif 'My custom error' in previous_error:
    sql_prompt += get_my_validation_error_feedback()
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_security.py

# Run with coverage
pytest --cov=src tests/

# Verbose output
pytest -v
```

### Writing Tests

**Example: Testing validation**
```python
# tests/test_validation.py
import pytest
from src.core.validation import validate_sql_query
from src.core.errors import SQLGenerationError

def test_forbidden_keyword():
    """Test that DROP keyword is blocked"""
    sql = "DROP TABLE users"
    allowed = {'users'}

    with pytest.raises(SQLGenerationError) as exc:
        validate_sql_query(sql, allowed)

    assert "Forbidden SQL keyword: DROP" in str(exc.value)

def test_valid_query():
    """Test that valid SELECT passes"""
    sql = 'SELECT * FROM users'
    allowed = {'users'}

    result = validate_sql_query(sql, allowed)
    assert result is True
```

### Manual Testing

**Test SQL generation:**
```bash
python -m src.cli
> Show me top 10 customers
```

**Test with specific dataset:**
```bash
# 1. Add CSV to data/
# 2. Update config/keys.json
# 3. Reload data
python -m src.data_pipeline.load_data
python -m src.data_pipeline.generate_schema
# 4. Test
langgraph dev
```

---

## Code Style

### Python (PEP 8 + Type Hints)

```python
from typing import Dict, List, Set, Optional

def process_data(
    input_data: List[Dict[str, str]],
    max_items: int = 10,
    filter_fn: Optional[callable] = None
) -> Dict[str, int]:
    """
    Process input data and return summary.

    Args:
        input_data: List of dictionaries to process
        max_items: Maximum number of items to return
        filter_fn: Optional filtering function

    Returns:
        Dictionary mapping keys to counts

    Raises:
        ValueError: If input_data is empty
    """
    if not input_data:
        raise ValueError("input_data cannot be empty")

    # Implementation...
    result: Dict[str, int] = {}
    return result
```

### TypeScript (Frontend)

```typescript
interface UserQuestion {
  content: string;
  timestamp: Date;
}

async function submitQuestion(question: UserQuestion): Promise<Response> {
  // Implementation...
}
```

### Documentation

- **Docstrings:** All public functions must have docstrings
- **Comments:** Explain *why*, not *what*
- **Type hints:** Use throughout Python code
- **Markdown:** Use for all documentation files

### Naming Conventions

```python
# Files
my_module.py         # snake_case
MyComponent.tsx      # PascalCase (React)

# Functions
def get_user_data()  # snake_case

# Classes
class SQLValidator   # PascalCase

# Constants
MAX_RETRIES = 3      # UPPER_CASE

# Variables
user_count = 0       # snake_case
```

---

## Common Tasks

### Changing LLM Provider

**From Cerebras to OpenAI:**
```python
# src/agent/nodes.py
from langchain_openai import ChatOpenAI

llm_sql = ChatOpenAI(
    model="gpt-4",
    temperature=0.1,
    api_key=os.getenv('OPENAI_API_KEY')
)
```

Update `.env`:
```bash
OPENAI_API_KEY=your_key_here
```

### Adding New Chart Type

1. **Update validation** in `nodes.py`:
```python
VALID_CHART_TYPES = {'bar', 'line', 'pie', 'scatter'}  # Add scatter
```

2. **Add chart generation logic**:
```python
if chart_type == 'scatter':
    fig = px.scatter(df, x=x_col, y=y_col, title=title)
```

3. **Test in frontend** (chart auto-renders via Plotly)

### Modifying Data Pipeline

**Add preprocessing step:**
```python
# src/data_pipeline/load_data.py

def preprocess_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Apply custom transformations"""
    df['new_column'] = df['existing'].apply(lambda x: ...)
    return df

# Use in load_data()
df = preprocess_csv(df)
```

### Adding PII Detection Rule

```python
# src/data_pipeline/pii_discovery.py

def is_pii_column(column_name: str, sample_values: List[str]) -> bool:
    # Add custom heuristics
    if 'ssn' in column_name.lower():
        return True

    # Use LLM for ambiguous cases
    # ...
```

---

## Debugging

### Enable Debug Logging

```python
# src/core/logger.py
logger = setup_logger('cadet.nodes', level=logging.DEBUG)
```

### Check LangGraph Traces

1. Ensure `LANGCHAIN_TRACING_V2=true` in `.env`
2. Visit https://smith.langchain.com
3. Find your run ID
4. View detailed trace

### Debug SQL Generation

**Check generated SQL:**
```bash
tail -f log.txt | grep "SQL query:"
```

**Check validation errors:**
```bash
grep "=== SQL Validation Failed ===" log.txt -A 10
```

### Debug Retry Logic

**Check retry count:**
```bash
grep "Retry" log.txt
# Output: "Retry 1/3: Added specific feedback..."
```

### Frontend Debugging

```bash
# Open browser console (F12)
# Check LangGraph client logs
```

### Database Debugging

```bash
# Connect to PostgreSQL
docker exec -it cadet-db psql -U myuser -d delivery_db

# Check tables
\dt

# View schema
\d+ table_name

# Run test query
SELECT * FROM customers LIMIT 5;
```

---

## Git Workflow

### Commit Messages

```bash
# Format: <type>: <description>

# Types:
feat: Add new feature
fix: Bug fix
docs: Documentation only
refactor: Code restructure
test: Add tests
chore: Maintenance tasks

# Examples:
git commit -m "feat: Add scatter chart support"
git commit -m "fix: Validation error retry loop"
git commit -m "docs: Update ERROR-HANDLING.md"
git commit -m "refactor: Extract feedbacks to separate module"
```

### Branch Naming

```bash
feature/scatter-charts
fix/validation-retry-bug
docs/architecture-guide
refactor/feedback-module
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Changes Made
- Added X feature
- Fixed Y bug
- Updated Z documentation

## Testing
- [ ] Manual testing completed
- [ ] Unit tests added
- [ ] Integration tests pass

## Related Issues
Closes #123
```

---

## Performance Profiling

### Python Profiling

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code
    result = expensive_function()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumtime')
    stats.print_stats(10)  # Top 10
```

### Database Query Profiling

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE customer_id = 123;
```

---

## Troubleshooting

### "Module not found" Error
```bash
# Ensure PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:/path/to/cadet"
```

### Database Connection Error
```bash
# Check if database is running
docker ps | grep cadet-db

# Restart database
docker-compose restart db
```

### Frontend Build Error
```bash
# Clear cache
cd frontend
rm -rf .next node_modules
pnpm install
pnpm dev
```

### LangGraph Server Won't Start
```bash
# Check port 2024 availability
lsof -i :2024

# Kill process if needed
kill -9 <PID>

# Restart
langgraph dev
```

---

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md) - System design and components
- [Error Handling Guide](ERROR-HANDLING.md) - Validation and retry logic
- README.md - User setup and usage

---

## Getting Help

- **Documentation:** Start with docs/ folder
- **Code Comments:** Read inline documentation
- **Logs:** Check log.txt for detailed traces
- **LangSmith:** View execution traces
- **Issues:** Check existing GitHub issues

---

**Last Updated:** 2026-01-11
