# Alert Creation System Tests

Comprehensive test suite for the alert-creation system covering API endpoints, business logic, data models, and integration scenarios.

## 🏗️ Test Structure

```
tests/
├── __init__.py                 # Test package
├── conftest.py                 # Shared fixtures and configuration
├── pytest.ini                 # Pytest configuration
├── requirements.txt            # Test dependencies
├── run_tests.py               # Test runner script
├── test_main.py               # FastAPI endpoint tests
├── test_sql_executor.py       # Database/SQL tests
├── test_alert_parser.py       # Alert parsing logic tests
├── test_integration.py        # End-to-end integration tests
└── test_utils.py              # Utility function tests
```

## 🚀 Quick Start

### Install Test Dependencies

```bash
cd alert-creation/tests
pip install -r requirements.txt
```

### Run All Tests

```bash
python run_tests.py
```

### Run Specific Test Categories

```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# API tests only
python run_tests.py --api

# Run with coverage report
python run_tests.py --coverage

# Skip slow tests
python run_tests.py --fast
```

### Run Individual Test Files

```bash
# Test specific module
python run_tests.py --file test_main.py

# Using pytest directly
pytest test_main.py -v

# Test specific function
pytest test_main.py::TestValidateAlertRuleEndpoint::test_validate_rule_success -v
```

## 📋 Test Categories

### 1. API Tests (`test_main.py`)
- **Data Models**: Transaction, Alert, request validation
- **Validate Endpoint**: `/alert-rules/validate` functionality
- **Generate Endpoint**: `/alert-rules/generate` functionality
- **Error Handling**: Malformed requests, validation errors
- **Edge Cases**: Empty rules, special characters, long inputs

### 2. SQL Executor Tests (`test_sql_executor.py`)
- **Core Functionality**: SQL execution, result formatting
- **Query Types**: Amount thresholds, categories, time-based, aggregations
- **Error Handling**: Database errors, syntax errors, permissions
- **Data Types**: Mixed data type handling
- **Performance**: Large result sets, connection issues

### 3. Alert Parser Tests (`test_alert_parser.py`)
- **Prompt Building**: Transaction data formatting, missing fields
- **Alert Type Detection**: Amount, category, location, merchant-based rules
- **Edge Cases**: Empty rules, special characters, multilingual input
- **Complex Rules**: Multi-condition alerts, ambiguous inputs

### 4. Integration Tests (`test_integration.py`)
- **End-to-End Workflows**: Complete validation → generation flow
- **Alert Types**: Amount thresholds, categories, complex rules
- **Error Recovery**: Invalid rules, malformed data
- **Performance**: Multiple requests, large data
- **Data Consistency**: ID preservation, user tracking

### 5. Utility Tests (`test_utils.py`)
- **Response Extraction**: Text processing, multiline handling
- **SQL Extraction**: Code blocks, CTE wrapping, formatting
- **LLM Client Selection**: Provider selection, environment handling
- **Robustness**: Malformed input, special characters, None handling

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)
- **Test Discovery**: Automatic test file and function detection
- **Coverage**: 70% minimum coverage requirement
- **Markers**: Categorize tests (unit, integration, api, slow)
- **Output**: Verbose reporting with HTML coverage

### Shared Fixtures (`conftest.py`)
- **Transaction Templates**: Base, dining, gas, high-amount transactions
- **Test Data**: User IDs, credit cards, dates
- **Mocks**: LLM responses, database connections, external services
- **Validators**: Data structure validation helpers

## 📊 Coverage and Quality

### Coverage Reports
```bash
# Generate HTML coverage report
python run_tests.py --coverage

# View report
open htmlcov/index.html
```

### Test Markers
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - End-to-end integration tests
- `@pytest.mark.api` - FastAPI endpoint tests
- `@pytest.mark.slow` - Performance/load tests
- `@pytest.mark.database` - Tests requiring database
- `@pytest.mark.llm` - Tests requiring LLM integration

## 🧪 Test Scenarios

### Alert Rule Validation
- ✅ Simple rules ("Alert when I spend > $100")
- ✅ Category-based ("Alert for dining purchases")
- ✅ Location-based ("Alert for out-of-state transactions")
- ✅ Complex rules ("Alert when I spend > $50 on dining in NYC")
- ✅ Invalid/ambiguous rules
- ✅ Edge cases (empty, special characters)

### Alert Generation
- ✅ Threshold triggers (amount, frequency)
- ✅ Category matches (dining, gas, retail)
- ✅ Location detection (state, city)
- ✅ Merchant-specific alerts
- ✅ Multi-condition rules
- ✅ Non-triggering scenarios

### Data Handling
- ✅ Transaction validation
- ✅ Date/time processing
- ✅ Currency and amount precision
- ✅ Special characters in merchant names
- ✅ Large data fields
- ✅ Missing optional fields

### Error Scenarios
- ✅ Malformed JSON requests
- ✅ Missing required fields
- ✅ Invalid data types
- ✅ Database connection errors
- ✅ LLM service failures
- ✅ Timeout handling

## 🔍 Debugging Tests

### Run Tests with Debug Output
```bash
pytest test_main.py -v -s --tb=long
```

### Test Specific Scenarios
```bash
# Test only validation endpoint
pytest -k "validate" -v

# Test only error scenarios
pytest -k "error" -v

# Test with specific transaction type
pytest -k "dining" -v
```

### Mock and Fixture Debugging
```bash
# See fixture values
pytest --fixtures

# Debug with pdb
pytest --pdb test_main.py::test_specific_function
```

## 🚧 Adding New Tests

### 1. Create Test File
```python
# test_new_feature.py
import pytest
from fastapi.testclient import TestClient

def test_new_functionality():
    # Test implementation
    assert True
```

### 2. Add Fixtures (if needed)
```python
# In conftest.py
@pytest.fixture
def new_test_data():
    return {"key": "value"}
```

### 3. Run New Tests
```bash
pytest test_new_feature.py -v
```

## 📈 Performance Testing

### Load Testing
```python
def test_multiple_requests():
    """Test system under load"""
    responses = []
    for i in range(100):
        response = client.post("/alert-rules/validate", json={"rule": f"Test rule {i}"})
        responses.append(response)
    
    # All should succeed
    assert all(r.status_code == 200 for r in responses)
```

### Timing Tests
```python
def test_response_time(performance_timer):
    """Test API response time"""
    performance_timer.start()
    response = client.post("/alert-rules/validate", json={"rule": "Test rule"})
    performance_timer.stop()
    
    assert response.status_code == 200
    assert performance_timer.elapsed < 5.0  # Max 5 seconds
```

## 🛡️ Security Testing

### Input Validation
- SQL injection attempts
- XSS payload handling
- Large payload processing
- Special character handling
- Unicode and encoding tests

### Error Information Disclosure
- Ensure errors don't leak sensitive data
- Validate error message format
- Check stack trace filtering

## 📝 Test Documentation

Each test file includes:
- **Module docstring**: Purpose and scope
- **Class docstrings**: Test category description
- **Method docstrings**: Specific test scenario
- **Inline comments**: Complex logic explanation
- **Assertions**: Clear expectation statements

## 🔄 Continuous Integration

The test suite is designed for CI/CD integration:
- **Fast execution**: Unit tests run in <30 seconds
- **Parallel execution**: Tests can run concurrently
- **Clear reporting**: JUnit XML and HTML reports
- **Coverage tracking**: Minimum 70% coverage
- **Exit codes**: Proper success/failure indication

---

Run the tests to ensure system reliability and catch regressions early! 🚀
