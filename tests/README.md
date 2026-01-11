# Tests

This directory contains unit tests for the Cadet SQL Agent.

## Structure

```
tests/
├── agent/
│   ├── test_routing.py    # Routing logic tests (critical)
│   ├── test_helpers.py    # Helper utilities tests
│   └── test_config.py     # Configuration tests
└── test_security.py       # Security validation tests
```

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-mock pytest-cov
```

### Run All Tests

```bash
# From project root
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Routing tests only
pytest tests/agent/test_routing.py -v

# Helpers tests only
pytest tests/agent/test_helpers.py -v

# Config tests only
pytest tests/agent/test_config.py -v
```

### Run Specific Test Classes

```bash
# SQL retry logic tests
pytest tests/agent/test_routing.py::TestDecideSQLRetryRoute -v

# PII masking tests
pytest tests/agent/test_helpers.py::TestApplyPIIMasking -v
```

### Run With Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src/agent --cov-report=html

# View report
open htmlcov/index.html
```

## Test Coverage

Current test coverage focuses on:

- **Routing Logic** (test_routing.py): Validates workflow routing decisions
  - Intent classification routing
  - SQL retry logic with Pyodide fallback
  - Pyodide analysis routing
  
- **Helper Functions** (test_helpers.py): Validates utility functions
  - Database engine caching
  - Schema loading and caching
  - PII masking logic

- **Configuration** (test_config.py): Validates LLM and constant setup
  - LLM instance initialisation
  - Temperature settings
  - Configuration constants

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_it_tests>`

### Example

```python
class TestMyFeature:
    """Test suite for my feature."""
    
    def test_feature_works_correctly(self):
        """Should do something when condition is met."""
        result = my_feature(input_data)
        assert result == expected_output
```

### Best Practises

1. **One assertion per test** (when possible)
2. **Clear test names** that describe expected behaviour
3. **Use mocks** to isolate unit under test
4. **Test edge cases** (None, empty, invalid inputs)
5. **Document with docstrings** explaining what's tested

## Continuous Integration

These tests should be run:

- Before committing changes
- In CI/CD pipeline
- After refactoring
- When adding new features

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running tests from project root:

```bash
cd /path/to/cadet
pytest tests/
```

### Module Not Found

Ensure all `__init__.py` files exist:

```bash
touch tests/__init__.py
touch tests/agent/__init__.py
```

### Mock Issues

If mocks aren't working, check the import path matches exactly:

```python
# Wrong
@patch('helpers.get_db_engine')

# Correct
@patch('src.agent.helpers.get_db_engine')
```
