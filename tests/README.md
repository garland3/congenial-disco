# AI Interview Assistant - Test Suite

This directory contains comprehensive tests for the AI Interview Assistant FastAPI application.

## Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── pytest.ini              # Pytest configuration
├── run_tests.py            # Test runner script
├── README.md               # This file
├── unit/                   # Unit tests
│   ├── test_llm_service.py # LLM service unit tests
│   └── test_models.py      # Database models unit tests
├── integration/            # Integration tests
│   ├── test_admin_api.py   # Admin API endpoint tests
│   ├── test_interview_api.py # Interview API endpoint tests
│   └── test_fastapi_app.py # FastAPI application tests
└── fixtures/               # Test fixtures and factories
    └── factories.py        # Factory Boy model factories
```

## Test Categories

### Unit Tests (`tests/unit/`)

**LLM Service Tests (`test_llm_service.py`)**
- Tests for question generation from goals
- Response evaluation logic
- Fallback mechanisms
- API error handling
- Mock LLM interactions

**Database Models Tests (`test_models.py`)**
- SQLAlchemy model creation and validation
- Pydantic model serialization/deserialization
- Model relationships
- Default values and constraints

### Integration Tests (`tests/integration/`)

**Admin API Tests (`test_admin_api.py`)**
- Template CRUD operations
- Template generation from goals
- Data validation and error handling
- Complete admin workflows

**Interview API Tests (`test_interview_api.py`)**
- Interview session management
- Chat functionality
- Progress tracking
- Complete interview workflows

**FastAPI App Tests (`test_fastapi_app.py`)**
- Application startup and configuration
- CORS middleware
- Error handling
- Performance characteristics

## Running Tests

### Prerequisites

Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Quick Start

```bash
# Run all tests
python tests/run_tests.py

# Check test dependencies
python tests/run_tests.py --check-deps

# Run specific test categories
python tests/run_tests.py --unit
python tests/run_tests.py --integration
python tests/run_tests.py --fast

# Run with coverage report
python tests/run_tests.py --coverage

# Run specific test file
python tests/run_tests.py --test unit/test_llm_service.py
```

### Using pytest directly

```bash
cd tests

# Run all tests
pytest

# Run unit tests only
pytest unit/

# Run integration tests only
pytest integration/

# Run with coverage
pytest --cov=backend/app --cov-report=html

# Run specific test
pytest unit/test_llm_service.py::TestLLMService::test_generate_questions_from_goals_success -v

# Run tests matching pattern
pytest -k "test_create_template"
```

## Test Configuration

### Environment

Tests use a separate SQLite database (`test.db`) that is created and destroyed for each test function. This ensures test isolation and prevents interference with development data.

### Fixtures

**Common Fixtures (defined in `conftest.py`):**
- `test_db`: Isolated test database session
- `client`: FastAPI test client with dependency overrides
- `mock_openai_client`: Mocked OpenAI client for LLM testing
- `sample_questions_schema`: Sample question schema for testing
- `sample_template_data`: Sample interview template data

**Factory Boy Factories (in `fixtures/factories.py`):**
- `InterviewTemplateFactory`: Creates test interview templates
- `InterviewSessionFactory`: Creates test interview sessions

### Mocking

Tests use `unittest.mock` and `pytest-mock` to mock external dependencies:

- **OpenAI API calls**: Mocked to avoid actual API calls and costs
- **LLM service responses**: Controlled responses for predictable testing
- **Database transactions**: Use test database for isolation

## Test Coverage

The test suite aims for high code coverage across:

- **Core business logic**: LLM service, response evaluation
- **API endpoints**: All admin and interview endpoints
- **Data models**: Database and Pydantic models
- **Error handling**: Validation, 404s, 500s
- **Edge cases**: Empty data, malformed requests, API failures

Current coverage can be viewed by running:
```bash
python tests/run_tests.py --coverage
```

Coverage report will be generated in `htmlcov/index.html`.

## Writing New Tests

### Unit Test Guidelines

1. **Test single units of functionality**
2. **Mock external dependencies**
3. **Use descriptive test names**: `test_function_name_condition_expected_result`
4. **Test both success and failure cases**
5. **Test edge cases and boundary conditions**

Example:
```python
def test_evaluate_response_sufficient_answer(self, llm_service, mock_openai_client):
    """Test response evaluation when answer is sufficient."""
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "SUFFICIENT"
    
    is_sufficient, feedback = await llm_service.evaluate_response(
        "What is your name?", "John Doe", "string"
    )
    
    assert is_sufficient is True
    assert feedback is None
```

### Integration Test Guidelines

1. **Test complete workflows**
2. **Use test database and client fixtures**
3. **Test API contracts and response formats**
4. **Verify database state changes**
5. **Test error conditions and status codes**

Example:
```python
def test_create_template_success(self, client, sample_template_data):
    """Test creating a new template."""
    response = client.post("/api/admin/templates", json=sample_template_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_template_data["name"]
    assert "id" in data
```

### Test Organization

- **Group related tests in classes**: `class TestLLMService:`
- **Use descriptive class and method names**
- **One assertion per test when possible**
- **Setup/teardown in fixtures, not in tests**

## Continuous Integration

Tests are designed to run in CI environments:

- **No external API dependencies** (all mocked)
- **Isolated test database** (created/destroyed per test)
- **Deterministic results** (no random data)
- **Fast execution** (unit tests < 1s each)

## Debugging Tests

### Common Issues

**Import Errors**
```bash
# Ensure backend is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

**Database Issues**
```bash
# Clean up test databases
rm -f tests/test.db
```

**Mock Issues**
```bash
# Run specific test with verbose output
pytest tests/unit/test_llm_service.py::TestLLMService::test_generate_questions_from_goals_success -v -s
```

### Test Debugging

1. **Use `-v` flag for verbose output**
2. **Use `-s` flag to see print statements**
3. **Add `import pdb; pdb.set_trace()` for debugging**
4. **Check test database state manually if needed**

## Performance Considerations

- **Unit tests should complete in < 1 second each**
- **Integration tests should complete in < 5 seconds each**
- **Use `@pytest.mark.slow` for tests that take longer**
- **Mock expensive operations (API calls, file I/O)**

## Best Practices

1. **Test behavior, not implementation**
2. **Use factory patterns for test data**
3. **Keep tests independent and isolated**
4. **Test edge cases and error conditions**
5. **Use meaningful assertions with custom messages**
6. **Keep test code clean and maintainable**
7. **Update tests when changing functionality**

## Troubleshooting

**Tests failing locally but passing in CI:**
- Check Python version compatibility
- Ensure all dependencies are installed
- Verify environment variables

**Slow test execution:**
- Use `--fast` flag to skip slow tests
- Check for unneeded API calls or database operations
- Profile tests with `pytest --durations=10`

**Coverage not reflecting changes:**
- Ensure test files are in correct locations
- Check that new code paths are covered
- Use `--cov-report=html` for detailed coverage view