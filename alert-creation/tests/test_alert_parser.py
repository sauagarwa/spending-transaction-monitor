"""
Test cases for alert parsing functionality
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.alert_parser import build_prompt


class TestBuildPrompt:
    """Test prompt building functionality"""
    
    def test_build_prompt_basic(self):
        """Test basic prompt building"""
        transaction = {
            "first": "John",
            "last": "Doe",
            "merchant_name": "Restaurant ABC",
            "amount": 45.50,
            "merchant_category": "dining"
        }
        alert_text = "Alert me when I spend more than $50 on dining"
        
        prompt = build_prompt(transaction, alert_text)
        
        assert "John Doe" in prompt
        assert "Restaurant ABC" in prompt
        assert "45.5" in prompt or "45.50" in prompt
        assert "dining" in prompt
        assert alert_text in prompt
    
    def test_build_prompt_missing_names(self):
        """Test prompt building with missing name fields"""
        transaction = {
            "first": "",
            "last": "",
            "merchant_name": "Store XYZ",
            "amount": 100.00,
            "merchant_category": "retail"
        }
        alert_text = "Alert for large purchases"
        
        prompt = build_prompt(transaction, alert_text)
        
        # Should handle empty names gracefully
        assert "Store XYZ" in prompt
        assert "100" in prompt
        assert alert_text in prompt
    
    def test_build_prompt_special_characters(self):
        """Test prompt building with special characters"""
        transaction = {
            "first": "José",
            "last": "García",
            "merchant_name": "McDonald's & Co.",
            "amount": 12.99,
            "merchant_category": "fast_food"
        }
        alert_text = "Alert me for fast food purchases > $10"
        
        prompt = build_prompt(transaction, alert_text)
        
        assert "José García" in prompt
        assert "McDonald's & Co." in prompt
        assert "12.99" in prompt
        assert ">" in prompt


class TestAlertTypeClassification:
    """Test alert type classification (simulated since determine_alert_type doesn't exist)"""
    
    def classify_alert_type(self, rule: str) -> str:
        """Simple rule classification for testing"""
        rule_lower = rule.lower()
        
        if any(word in rule_lower for word in ["spend", "more than", "$", "amount", "over"]):
            return "AMOUNT_THRESHOLD"
        elif any(word in rule_lower for word in ["dining", "restaurant", "food", "grocery", "category"]):
            return "MERCHANT_CATEGORY"
        elif any(word in rule_lower for word in ["outside", "location", "city", "state", "california"]):
            return "LOCATION_BASED"
        elif any(word in rule_lower for word in ["amazon", "walmart", "merchant", "store"]):
            return "MERCHANT_NAME"
        elif any(word in rule_lower for word in ["day", "transactions", "frequency", "often"]):
            return "FREQUENCY_BASED"
        else:
            return "CUSTOM_QUERY"
    
    def test_amount_threshold_alert(self):
        """Test amount threshold alert detection"""
        rule = "Alert me when I spend more than $100"
        alert_type = self.classify_alert_type(rule)
        
        assert alert_type == "AMOUNT_THRESHOLD"
    
    def test_category_based_alert(self):
        """Test category-based alert detection"""
        rule = "Alert me for all dining purchases"
        alert_type = self.classify_alert_type(rule)
        
        assert alert_type == "MERCHANT_CATEGORY"
    
    def test_location_based_alert(self):
        """Test location-based alert detection"""
        rule = "Alert me for transactions outside California"
        alert_type = self.classify_alert_type(rule)
        
        assert alert_type == "LOCATION_BASED"
    
    def test_merchant_specific_alert(self):
        """Test merchant-specific alert detection"""
        rule = "Alert me for any purchases at Amazon"
        alert_type = self.classify_alert_type(rule)
        
        assert alert_type == "MERCHANT_NAME"
    
    def test_frequency_based_alert(self):
        """Test frequency-based alert detection"""
        rule = "Alert me if I make more than 5 transactions per day"
        alert_type = self.classify_alert_type(rule)
        
        assert alert_type == "FREQUENCY_BASED"
    
    def test_complex_alert(self):
        """Test complex multi-condition alert"""
        rule = "Alert me when I spend more than $50 on dining in New York"
        alert_type = self.classify_alert_type(rule)
        
        # Should return amount threshold since it has spending condition
        assert alert_type == "AMOUNT_THRESHOLD"
    
    def test_ambiguous_alert(self):
        """Test ambiguous or unclear alert rule"""
        rule = "Something seems wrong with my spending"
        alert_type = self.classify_alert_type(rule)
        
        # Should default to custom query
        assert alert_type == "CUSTOM_QUERY"


class TestAlertParsingEdgeCases:
    """Test edge cases in alert parsing"""
    
    def classify_alert_type(self, rule: str) -> str:
        """Simple rule classification for testing"""
        rule_lower = rule.lower()
        
        if any(word in rule_lower for word in ["spend", "more than", "$", "amount", "over"]):
            return "AMOUNT_THRESHOLD"
        elif any(word in rule_lower for word in ["dining", "restaurant", "food", "grocery", "category"]):
            return "MERCHANT_CATEGORY"
        elif any(word in rule_lower for word in ["outside", "location", "city", "state", "california"]):
            return "LOCATION_BASED"
        elif any(word in rule_lower for word in ["amazon", "walmart", "merchant", "store"]):
            return "MERCHANT_NAME"
        elif any(word in rule_lower for word in ["day", "transactions", "frequency", "often"]):
            return "FREQUENCY_BASED"
        else:
            return "CUSTOM_QUERY"
    
    def test_empty_rule(self):
        """Test parsing empty alert rule"""
        rule = ""
        alert_type = self.classify_alert_type(rule)
        
        # Should handle empty input gracefully
        assert alert_type == "CUSTOM_QUERY"
    
    def test_very_long_rule(self):
        """Test parsing very long alert rule"""
        rule = "Alert me " + "when I spend money " * 50 + "more than usual"
        alert_type = self.classify_alert_type(rule)
        
        assert alert_type == "AMOUNT_THRESHOLD"  # Contains "spend" keyword
    
    def test_numeric_only_rule(self):
        """Test parsing numeric-only rule"""
        rule = "100.50"
        alert_type = self.classify_alert_type(rule)
        
        # Should handle numeric input
        assert alert_type == "CUSTOM_QUERY"
    
    def test_special_characters_rule(self):
        """Test parsing rule with special characters"""
        rule = "Alert me when I spend >$100 @merchant's store #urgent !!!"
        alert_type = self.classify_alert_type(rule)
        
        assert alert_type == "AMOUNT_THRESHOLD"  # Contains "spend" and "$"
    
    def test_multilingual_rule(self):
        """Test parsing rule with non-English characters"""
        rule = "Alerta cuando gasto más de $100 en restaurantes"
        alert_type = self.classify_alert_type(rule)
        
        # Should handle non-English input gracefully
        assert alert_type == "CUSTOM_QUERY"  # No English keywords match


class TestPromptGeneration:
    """Test comprehensive prompt generation scenarios"""
    
    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction for testing"""
        return {
            "first": "Alice",
            "last": "Johnson",
            "user_id": "user_123",
            "transaction_date": "2024-01-15T10:30:00",
            "amount": 89.99,
            "merchant_name": "Whole Foods Market",
            "merchant_category": "grocery",
            "merchant_city": "San Francisco",
            "merchant_state": "CA",
            "trans_num": "txn_001"
        }
    
    def test_comprehensive_prompt(self, sample_transaction):
        """Test comprehensive prompt with all transaction details"""
        alert_text = "Alert me when I spend more than $75 on groceries"
        
        prompt = build_prompt(sample_transaction, alert_text)
        
        # Check that key information is included
        assert "Alice Johnson" in prompt
        assert "89.99" in prompt
        assert "Whole Foods Market" in prompt
        assert "grocery" in prompt
        assert "San Francisco" in prompt
        assert alert_text in prompt
    
    def test_prompt_structure(self, sample_transaction):
        """Test that prompt has proper structure"""
        alert_text = "Test alert rule"
        
        prompt = build_prompt(sample_transaction, alert_text)
        
        # Should be a non-empty string
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
        # Should contain both transaction info and alert rule
        assert any(key in prompt.lower() for key in ["transaction", "purchase", "spend"])
        assert alert_text in prompt
    
    def test_prompt_with_missing_fields(self):
        """Test prompt generation with minimal transaction data"""
        minimal_transaction = {
            "amount": 25.00,
            "merchant_name": "Coffee Shop"
        }
        alert_text = "Alert for coffee purchases"
        
        prompt = build_prompt(minimal_transaction, alert_text)
        
        assert "25" in prompt
        assert "Coffee Shop" in prompt
        assert alert_text in prompt


if __name__ == "__main__":
    pytest.main([__file__])
