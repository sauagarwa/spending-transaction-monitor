"""
Integration tests for the complete alert system
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestEndToEndAlertFlow:
    """Test complete alert workflow from rule validation to alert generation"""
    
    @pytest.fixture
    def dining_transaction(self):
        """Sample dining transaction"""
        return {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "transaction_date": "2024-01-15T19:30:00",
            "credit_card_num": "1234-5678-9101-1121",
            "amount": 125.50,
            "currency": "USD",
            "description": "Dinner with friends",
            "merchant_name": "Fancy Restaurant",
            "merchant_category": "dining",
            "merchant_city": "San Francisco",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.7749,
            "merchant_longitude": -122.4194,
            "merchant_zipcode": 94102,
            "trans_num": "txn_dining_001",
            "authorization_code": "AUTH123456",
            "reference_number": "REF789012",
            "first_name": "John",
            "last_name": "Doe"
        }
    
    @pytest.fixture
    def gas_transaction(self):
        """Sample gas station transaction"""
        return {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "transaction_date": "2024-01-16T08:15:00",
            "credit_card_num": "1234-5678-9101-1121",
            "amount": 65.00,
            "currency": "USD",
            "description": "Gas fill-up",
            "merchant_name": "Shell Gas Station",
            "merchant_category": "gas_station",
            "merchant_city": "San Francisco",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.7849,
            "merchant_longitude": -122.4094,
            "merchant_zipcode": 94103,
            "trans_num": "txn_gas_001",
            "authorization_code": "AUTH789012",
            "reference_number": "REF345678",
            "first_name": "John",
            "last_name": "Doe"
        }
    
    def test_amount_threshold_workflow(self, dining_transaction):
        """Test complete workflow for amount threshold alerts"""
        rule = "Alert me when I spend more than $100 on dining"
        
        # Step 1: Validate the rule
        validate_response = client.post("/alert-rules/validate", json={"rule": rule})
        assert validate_response.status_code == 200
        
        validate_data = validate_response.json()
        print(f"Validation result: {validate_data['status']}")
        
        # Step 2: Generate alert with transaction that should trigger
        generate_request = {
            "rule": rule,
            "transaction": dining_transaction
        }
        
        generate_response = client.post("/alert-rules/generate", json=generate_request)
        assert generate_response.status_code == 200
        
        generate_data = generate_response.json()
        print(f"Alert generation result: {generate_data['status']}")
        
        # Verify response structure
        assert "status" in generate_data
        assert "transaction_id" in generate_data
        assert generate_data["transaction_id"] == "txn_dining_001"
    
    def test_category_based_workflow(self, gas_transaction):
        """Test complete workflow for category-based alerts"""
        rule = "Alert me for any gas station purchases"
        
        # Step 1: Validate the rule
        validate_response = client.post("/alert-rules/validate", json={"rule": rule})
        assert validate_response.status_code == 200
        
        # Step 2: Generate alert
        generate_request = {
            "rule": rule,
            "transaction": gas_transaction
        }
        
        generate_response = client.post("/alert-rules/generate", json=generate_request)
        assert generate_response.status_code == 200
        
        generate_data = generate_response.json()
        assert generate_data["transaction_id"] == "txn_gas_001"
    
    def test_complex_rule_workflow(self, dining_transaction):
        """Test workflow with complex multi-condition rule"""
        rule = "Alert me when I spend more than $100 on dining in San Francisco"
        
        # Step 1: Validate complex rule
        validate_response = client.post("/alert-rules/validate", json={"rule": rule})
        assert validate_response.status_code == 200
        
        # Step 2: Test with matching transaction
        generate_request = {
            "rule": rule,
            "transaction": dining_transaction
        }
        
        generate_response = client.post("/alert-rules/generate", json=generate_request)
        assert generate_response.status_code == 200
        
        # Step 3: Test with non-matching transaction (change location)
        non_matching_transaction = dining_transaction.copy()
        non_matching_transaction["merchant_city"] = "Los Angeles"
        non_matching_transaction["trans_num"] = "txn_la_001"
        
        generate_request_2 = {
            "rule": rule,
            "transaction": non_matching_transaction
        }
        
        generate_response_2 = client.post("/alert-rules/generate", json=generate_request_2)
        assert generate_response_2.status_code == 200


class TestErrorRecovery:
    """Test system behavior under error conditions"""
    
    def test_invalid_rule_then_valid_transaction(self):
        """Test system recovery from invalid rule validation"""
        # Step 1: Try to validate an invalid/unclear rule
        invalid_rule = "asdfghjkl random text 12345"
        validate_response = client.post("/alert-rules/validate", json={"rule": invalid_rule})
        assert validate_response.status_code == 200  # Should handle gracefully
        
        # Step 2: Use a valid rule with valid transaction
        valid_rule = "Alert me when I spend more than $50"
        valid_transaction = {
            "user_id": "test_user",
            "transaction_date": "2024-01-15T10:30:00",
            "credit_card_num": "1234",
            "amount": 75.00,
            "currency": "USD",
            "description": "Test purchase",
            "merchant_name": "Test Store",
            "merchant_category": "retail",
            "merchant_city": "Test City",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.0,
            "merchant_longitude": -122.0,
            "merchant_zipcode": 12345,
            "trans_num": "test_txn",
            "authorization_code": "AUTH",
            "reference_number": "REF",
            "first_name": "Test",
            "last_name": "User"
        }
        
        generate_request = {
            "rule": valid_rule,
            "transaction": valid_transaction
        }
        
        generate_response = client.post("/alert-rules/generate", json=generate_request)
        assert generate_response.status_code == 200
    
    def test_malformed_requests_handling(self):
        """Test handling of malformed requests"""
        # Test completely empty request
        response = client.post("/alert-rules/validate", json={})
        assert response.status_code == 422
        
        # Test request with wrong field names
        response = client.post("/alert-rules/validate", json={"wrong_field": "value"})
        assert response.status_code == 422
        
        # Test generate alert with missing transaction
        response = client.post("/alert-rules/generate", json={"rule": "test rule"})
        assert response.status_code == 422


class TestPerformance:
    """Test system performance characteristics"""
    
    def test_multiple_concurrent_validations(self):
        """Test handling multiple rule validations"""
        rules = [
            "Alert me when I spend more than $100",
            "Alert me for dining purchases",
            "Alert me for transactions outside California",
            "Alert me when I make more than 3 purchases per day",
            "Alert me for any purchase over my average spending"
        ]
        
        responses = []
        for rule in rules:
            response = client.post("/alert-rules/validate", json={"rule": rule})
            responses.append(response)
        
        # All requests should complete successfully
        for response in responses:
            assert response.status_code == 200
    
    def test_large_transaction_data(self):
        """Test handling of transaction with large data fields"""
        large_transaction = {
            "user_id": "test_user_with_very_long_id_" + "x" * 100,
            "transaction_date": "2024-01-15T10:30:00",
            "credit_card_num": "1234-5678-9101-1121",
            "amount": 99.99,
            "currency": "USD",
            "description": "Very long description " + "text " * 100,
            "merchant_name": "Very Long Merchant Name " + "Store " * 20,
            "merchant_category": "retail",
            "merchant_city": "San Francisco",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.7749,
            "merchant_longitude": -122.4194,
            "merchant_zipcode": 94102,
            "trans_num": "txn_large_data_test",
            "authorization_code": "AUTH" + "1" * 50,
            "reference_number": "REF" + "2" * 50,
            "first_name": "VeryLongFirstName" + "a" * 30,
            "last_name": "VeryLongLastName" + "b" * 30
        }
        
        request = {
            "rule": "Alert me for large transactions",
            "transaction": large_transaction
        }
        
        response = client.post("/alert-rules/generate", json=request)
        assert response.status_code == 200


class TestDataConsistency:
    """Test data consistency across different operations"""
    
    def test_transaction_id_consistency(self):
        """Test that transaction IDs are preserved throughout the workflow"""
        transaction = {
            "user_id": "consistency_test_user",
            "transaction_date": "2024-01-15T10:30:00",
            "credit_card_num": "1234-5678-9101-1121",
            "amount": 55.55,
            "currency": "USD", 
            "description": "Consistency test",
            "merchant_name": "Test Merchant",
            "merchant_category": "test",
            "merchant_city": "Test City",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.0,
            "merchant_longitude": -122.0,
            "merchant_zipcode": 12345,
            "trans_num": "UNIQUE_TXN_ID_12345",
            "authorization_code": "AUTH123",
            "reference_number": "REF456",
            "first_name": "Test",
            "last_name": "User"
        }
        
        request = {
            "rule": "Alert me for any transaction",
            "transaction": transaction
        }
        
        response = client.post("/alert-rules/generate", json=request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["transaction_id"] == "UNIQUE_TXN_ID_12345"
    
    def test_user_id_consistency(self):
        """Test that user IDs are handled consistently"""
        user_id = "CONSISTENT_USER_ID_789"
        
        transaction = {
            "user_id": user_id,
            "transaction_date": "2024-01-15T10:30:00",
            "credit_card_num": "1234-5678-9101-1121",
            "amount": 42.42,
            "currency": "USD",
            "description": "User ID test",
            "merchant_name": "Test Store",
            "merchant_category": "test",
            "merchant_city": "Test City",
            "merchant_state": "CA",
            "merchant_country": "US",
            "merchant_latitude": 37.0,
            "merchant_longitude": -122.0,
            "merchant_zipcode": 12345,
            "trans_num": "txn_user_test",
            "authorization_code": "AUTH",
            "reference_number": "REF",
            "first_name": "Test",
            "last_name": "User"
        }
        
        request = {
            "rule": "Alert me for test transactions",
            "transaction": transaction
        }
        
        response = client.post("/alert-rules/generate", json=request)
        assert response.status_code == 200
        
        data = response.json()
        if data["status"] == "triggered" and "alert" in data:
            assert data["alert"]["user_id"] == user_id


if __name__ == "__main__":
    pytest.main([__file__])
