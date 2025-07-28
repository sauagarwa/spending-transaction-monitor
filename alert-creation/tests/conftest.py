"""
Pytest configuration and shared fixtures for alert-creation tests
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_user_id():
    """Standard test user ID for consistent testing"""
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture(scope="session")
def test_credit_card():
    """Standard test credit card for consistent testing"""
    return "1234-5678-9101-1121"


@pytest.fixture
def base_transaction():
    """Base transaction template for testing"""
    return {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "transaction_date": "2024-01-15T10:30:00",
        "credit_card_num": "1234-5678-9101-1121",
        "amount": 50.00,
        "currency": "USD",
        "description": "Test transaction",
        "merchant_name": "Test Merchant",
        "merchant_category": "test",
        "merchant_city": "San Francisco",
        "merchant_state": "CA",
        "merchant_country": "US",
        "merchant_latitude": 37.7749,
        "merchant_longitude": -122.4194,
        "merchant_zipcode": 94102,
        "trans_num": "txn_test_001",
        "authorization_code": "AUTH123",
        "reference_number": "REF456",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def dining_transaction(base_transaction):
    """Dining transaction for restaurant/food testing"""
    transaction = base_transaction.copy()
    transaction.update({
        "amount": 85.50,
        "merchant_name": "Gourmet Restaurant",
        "merchant_category": "dining",
        "description": "Dinner with friends",
        "trans_num": "txn_dining_001"
    })
    return transaction


@pytest.fixture
def gas_transaction(base_transaction):
    """Gas station transaction for fuel testing"""
    transaction = base_transaction.copy()
    transaction.update({
        "amount": 65.00,
        "merchant_name": "Shell Gas Station", 
        "merchant_category": "gas_station",
        "description": "Fuel fill-up",
        "trans_num": "txn_gas_001"
    })
    return transaction


@pytest.fixture
def high_amount_transaction(base_transaction):
    """High amount transaction for threshold testing"""
    transaction = base_transaction.copy()
    transaction.update({
        "amount": 1500.00,
        "merchant_name": "Electronics Store",
        "merchant_category": "electronics",
        "description": "Laptop purchase",
        "trans_num": "txn_expensive_001"
    })
    return transaction


@pytest.fixture
def out_of_state_transaction(base_transaction):
    """Out of state transaction for location testing"""
    transaction = base_transaction.copy()
    transaction.update({
        "merchant_city": "New York",
        "merchant_state": "NY",
        "merchant_latitude": 40.7128,
        "merchant_longitude": -74.0060,
        "merchant_zipcode": 10001,
        "trans_num": "txn_ny_001"
    })
    return transaction


@pytest.fixture
def recent_transaction_date():
    """Recent transaction date for time-based testing"""
    return datetime.now() - timedelta(hours=2)


@pytest.fixture
def old_transaction_date():
    """Old transaction date for historical testing"""
    return datetime.now() - timedelta(days=30)


@pytest.fixture
def sample_alert_rules():
    """Collection of sample alert rules for testing"""
    return [
        "Alert me when I spend more than $100",
        "Alert me for any dining purchases over $50",
        "Alert me for transactions outside California",
        "Alert me for gas station purchases",
        "Alert me when I make more than 3 purchases in a day",
        "Alert me if I spend more than my weekly average",
        "Alert me for any purchase at Amazon",
        "Alert me for international transactions",
        "Alert me for late night purchases after 11 PM",
        "Alert me when I spend more than $200 on groceries in a week"
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    def _mock_response(should_trigger=True, alert_type="AMOUNT_THRESHOLD", message="Test alert"):
        return {
            "should_trigger": should_trigger,
            "alert_type": alert_type,
            "message": message,
            "severity": "warning" if should_trigger else "info",
            "confidence": 0.85
        }
    return _mock_response


@pytest.fixture
def mock_sql_results():
    """Mock SQL query results for testing"""
    return [
        ("txn_001", 100.50, "Restaurant ABC", "dining"),
        ("txn_002", 75.25, "Gas Station", "gas_station"),
        ("txn_003", 250.00, "Electronics Store", "electronics")
    ]


# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Ensure test environment variables
    os.environ.setdefault("LLM_PROVIDER", "openai")
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    
    yield
    
    # Cleanup after tests
    # Remove test-specific environment variables if needed
    pass


# Mock fixtures for external dependencies
@pytest.fixture
def mock_parse_alert_graph():
    """Mock parse_alert_graph for testing"""
    with patch('parse_alert_graph.app') as mock_app:
        mock_app.invoke.return_value = {
            "status": "parsed",
            "alert_type": "AMOUNT_THRESHOLD",
            "conditions": {"amount_threshold": 100.00},
            "sql_query": "SELECT * FROM transactions WHERE amount > 100"
        }
        yield mock_app


@pytest.fixture
def mock_generate_alert_graph():
    """Mock generate_alert_graph for testing"""
    with patch('generate_alert_graph.app') as mock_app:
        mock_app.invoke.return_value = {
            "should_trigger": True,
            "alert_type": "AMOUNT_THRESHOLD",
            "message": "You spent $150.00 at Test Merchant, which exceeds your $100 threshold",
            "severity": "warning"
        }
        yield mock_app


@pytest.fixture
def mock_database_connection():
    """Mock database connection for SQL testing"""
    with patch('agents.sql_executor.conn') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("test_result", 123.45)]
        mock_conn.cursor.return_value = mock_cursor
        yield mock_conn


# Performance testing helpers
@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Data validation helpers
@pytest.fixture
def validate_transaction_data():
    """Helper to validate transaction data structure"""
    def _validate(transaction):
        required_fields = [
            "user_id", "transaction_date", "amount", "merchant_name",
            "merchant_category", "trans_num"
        ]
        
        for field in required_fields:
            assert field in transaction, f"Missing required field: {field}"
        
        assert isinstance(transaction["amount"], (int, float)), "Amount must be numeric"
        assert transaction["amount"] >= 0, "Amount must be non-negative"
        assert len(transaction["user_id"]) > 0, "User ID cannot be empty"
        
        return True
    
    return _validate


@pytest.fixture
def validate_alert_data():
    """Helper to validate alert data structure"""
    def _validate(alert):
        required_fields = ["user_id", "merchant", "type", "description"]
        
        for field in required_fields:
            assert field in alert, f"Missing required field: {field}"
        
        valid_severities = ["info", "warning", "error", "critical"]
        if "severity" in alert:
            assert alert["severity"] in valid_severities, f"Invalid severity: {alert['severity']}"
        
        return True
    
    return _validate
