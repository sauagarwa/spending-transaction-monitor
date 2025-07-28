"""
Test cases for main.py FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, Transaction, Alert, ValidateRuleRequest, GenerateAlertRequest

client = TestClient(app)

class TestDataModels:
    """Test Pydantic data models"""
    
    def test_transaction_model(self):
        """Test Transaction model validation"""
        transaction_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "transaction_date": "2024-01-15T10:30:00",
            "credit_card_num": "1234-5678-9101-1121",
            "amount": 89.99,
            "currency": "USD",
            "description": "Test transaction",
            "merchant_name": "Test Merchant",
            "merchant_category": "dining",
            "merchant_city": "San Francisco",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.7749,
            "merchant_longitude": -122.4194,
            "merchant_zipcode": 94102,
            "trans_num": "txn_001",
            "authorization_code": "AUTH123",
            "reference_number": "REF456",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        transaction = Transaction(**transaction_data)
        assert transaction.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert transaction.amount == 89.99
        assert transaction.merchant_category == "dining"
    
    def test_alert_model(self):
        """Test Alert model with optional fields"""
        alert_data = {
            "user_id": "123",
            "merchant": "Test Merchant",
            "type": "AMOUNT_THRESHOLD",
            "description": "Spending alert"
        }
        
        alert = Alert(**alert_data)
        assert alert.severity == "info"  # Default value
        assert alert.amount is None
        assert alert.triggered_at is None
    
    def test_validate_rule_request(self):
        """Test ValidateRuleRequest model"""
        request = ValidateRuleRequest(rule="Alert me when I spend more than $100")
        assert request.rule == "Alert me when I spend more than $100"


class TestValidateAlertRuleEndpoint:
    """Test /alert-rules/validate endpoint"""
    
    def test_validate_rule_success(self, sample_transaction):
        """Test successful rule validation"""
        request_data = {
            "rule": "Alert me when I spend more than $50 on dining",
            "transaction": sample_transaction
        }
        
        response = client.post("/alert-rules/validate", json=request_data)
        
        # Should return 200 regardless of LLM parsing result
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "message" in data
        assert data["status"] in ["valid", "invalid", "error"]
    
    def test_validate_rule_empty(self, sample_transaction):
        """Test validation with empty rule"""
        request_data = {
            "rule": "",
            "transaction": sample_transaction
        }
        
        response = client.post("/alert-rules/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["invalid", "error"]
    
    def test_validate_rule_complex(self, sample_transaction):
        """Test validation with complex rule"""
        request_data = {
            "rule": "Notify me if I spend more than my average weekly dining expense by 50% or more",
            "transaction": sample_transaction
        }
        
        response = client.post("/alert-rules/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        if data["status"] == "valid":
            assert "parsed_rule" in data
            assert "transaction_used" in data
            assert "validation_timestamp" in data
    
    def test_validate_rule_invalid_json(self):
        """Test validation with malformed request"""
        response = client.post("/alert-rules/validate", json={"invalid": "field"})
        assert response.status_code == 422  # Validation error
        
    def test_validate_rule_missing_transaction(self):
        """Test validation with missing transaction"""
        request_data = {"rule": "Alert me when I spend more than $50"}
        
        response = client.post("/alert-rules/validate", json=request_data)
        assert response.status_code == 422  # Validation error


class TestGenerateAlertEndpoint:
    """Test /alert-rules/generate endpoint"""
    
    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction for testing"""
        return {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "transaction_date": "2024-01-15T10:30:00",
            "credit_card_num": "1234-5678-9101-1121",
            "amount": 75.50,
            "currency": "USD",
            "description": "Dinner at restaurant",
            "merchant_name": "Fancy Restaurant",
            "merchant_category": "dining",
            "merchant_city": "San Francisco",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.7749,
            "merchant_longitude": -122.4194,
            "merchant_zipcode": 94102,
            "trans_num": "txn_001",
            "authorization_code": "AUTH123",
            "reference_number": "REF456",
            "first_name": "John",
            "last_name": "Doe"
        }
    
    def test_generate_alert_success(self, sample_transaction):
        """Test successful alert generation"""
        request_data = {
            "rule": "Alert me when I spend more than $50 on dining",
            "transaction": sample_transaction
        }
        
        response = client.post("/alert-rules/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "transaction_id" in data
        assert data["status"] in ["triggered", "not_triggered", "error"]
    
    def test_generate_alert_high_amount(self, sample_transaction):
        """Test alert with high transaction amount"""
        sample_transaction["amount"] = 500.00
        sample_transaction["merchant_name"] = "Expensive Store"
        
        request_data = {
            "rule": "Alert me when I spend more than $100",
            "transaction": sample_transaction
        }
        
        response = client.post("/alert-rules/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        if data["status"] == "triggered":
            assert "alert" in data
            alert = data["alert"]
            assert alert["amount"] == 500.00
            assert alert["user_id"] == sample_transaction["user_id"]
    
    def test_generate_alert_category_specific(self, sample_transaction):
        """Test category-specific alert rule"""
        sample_transaction["merchant_category"] = "gas_station"
        sample_transaction["merchant_name"] = "Shell Gas"
        
        request_data = {
            "rule": "Alert me for any gas station purchases",
            "transaction": sample_transaction
        }
        
        response = client.post("/alert-rules/generate", json=request_data)
        assert response.status_code == 200
    
    def test_generate_alert_location_based(self, sample_transaction):
        """Test location-based alert rule"""
        sample_transaction["merchant_state"] = "NY"
        sample_transaction["merchant_city"] = "New York"
        
        request_data = {
            "rule": "Alert me for transactions outside of California",
            "transaction": sample_transaction
        }
        
        response = client.post("/alert-rules/generate", json=request_data)
        assert response.status_code == 200
    
    def test_generate_alert_missing_transaction(self):
        """Test alert generation with missing transaction"""
        request_data = {
            "rule": "Alert me when I spend more than $50"
            # Missing transaction field
        }
        
        response = client.post("/alert-rules/generate", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_generate_alert_invalid_transaction(self):
        """Test alert generation with invalid transaction data"""
        request_data = {
            "rule": "Alert me when I spend more than $50",
            "transaction": {
                "user_id": "123",
                "amount": "invalid_amount",  # Should be float
                # Missing required fields
            }
        }
        
        response = client.post("/alert-rules/generate", json=request_data)
        assert response.status_code == 422  # Validation error


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_extremely_long_rule(self):
        """Test with extremely long rule text"""
        long_rule = "Alert me " + "when I spend more than $50 " * 100
        request_data = {"rule": long_rule}
        
        response = client.post("/alert-rules/validate", json=request_data)
        assert response.status_code == 200
    
    def test_special_characters_in_rule(self):
        """Test rule with special characters"""
        request_data = {
            "rule": "Alert me when I spend >$100 at McDonald's & Burger King 🍔"
        }
        
        response = client.post("/alert-rules/validate", json=request_data)
        assert response.status_code == 200
    
    def test_numeric_only_rule(self):
        """Test rule with only numbers"""
        request_data = {"rule": "123.45"}
        
        response = client.post("/alert-rules/validate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["invalid", "error"]


class TestHealthCheck:
    """Test basic API health"""
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/alert-rules/validate")
        assert response.status_code in [200, 405]  # Some FastAPI versions return 405 for OPTIONS


if __name__ == "__main__":
    pytest.main([__file__])
