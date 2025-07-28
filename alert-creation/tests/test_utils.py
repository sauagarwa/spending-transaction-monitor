"""
Test cases for utility functions
"""
import pytest
import sys
import os
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.utils import extract_response, extract_sql, get_llm_client


class TestExtractResponse:
    """Test response extraction utility"""
    
    def test_extract_response_basic(self):
        """Test basic response extraction"""
        response = "This is a test response with some content."
        result = extract_response(response)
        
        assert result == response.strip()
    
    def test_extract_response_multiline(self):
        """Test extraction with multiline response"""
        response = """
        Line 1
        Line 2
        Line 3
        """
        result = extract_response(response)
        
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    
    def test_extract_response_empty(self):
        """Test extraction with empty response"""
        response = ""
        result = extract_response(response)
        
        assert result == ""
    
    def test_extract_response_whitespace(self):
        """Test extraction with whitespace-only response"""
        response = "   \n\t   "
        result = extract_response(response)
        
        assert result == ""


class TestExtractSQL:
    """Test SQL extraction utility"""
    
    def test_extract_sql_basic(self):
        """Test basic SQL extraction"""
        sql = "SELECT * FROM transactions WHERE amount > 100"
        result = extract_sql(sql)
        
        assert result == sql.strip()
    
    def test_extract_sql_with_code_block(self):
        """Test SQL extraction from code block"""
        sql_input = """
        Here's the SQL query:
        ```sql
        SELECT user_id, amount, merchant_name
        FROM transactions
        WHERE amount > 50
        ORDER BY amount DESC
        ```
        """
        
        result = extract_sql(sql_input)
        
        assert "SELECT user_id, amount, merchant_name" in result
        assert "FROM transactions" in result
        assert "WHERE amount > 50" in result
        assert "```" not in result
    
    def test_extract_sql_with_think_blocks(self):
        """Test SQL extraction with thinking blocks"""
        sql_input = """
        <think>
        I need to find transactions over $50
        </think>
        SELECT * FROM transactions WHERE amount > 50
        """
        
        result = extract_sql(sql_input)
        
        assert "SELECT * FROM transactions WHERE amount > 50" in result
        assert "<think>" not in result
        assert "</think>" not in result
    
    def test_extract_sql_with_subquery_wrapping(self):
        """Test CTE wrapping for subqueries"""
        sql_input = "SELECT * FROM (SELECT user_id, SUM(amount) FROM transactions GROUP BY user_id)"
        
        result = extract_sql(sql_input)
        
        # Should wrap with CTE if it contains FROM ( but no WITH
        if "FROM (" in sql_input.upper() and not sql_input.strip().upper().startswith("WITH"):
            assert "WITH subquery AS" in result
        else:
            assert result.strip() == sql_input.strip()
    
    def test_extract_sql_already_cte(self):
        """Test SQL that already has CTE"""
        sql_input = """
        WITH monthly_spending AS (
            SELECT user_id, SUM(amount) as total
            FROM transactions
            WHERE transaction_date >= '2024-01-01'
            GROUP BY user_id
        )
        SELECT * FROM monthly_spending WHERE total > 1000
        """
        
        result = extract_sql(sql_input)
        
        # Should not double-wrap CTE
        assert result.count("WITH") == 1
        assert "WITH monthly_spending AS" in result
    
    def test_extract_sql_complex_formatting(self):
        """Test SQL extraction with complex formatting"""
        sql_input = """
        <think>Need to analyze spending patterns</think>
        
        ```sql
        SELECT 
            user_id,
            merchant_category,
            COUNT(*) as transaction_count,
            AVG(amount) as avg_amount
        FROM transactions 
        WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY user_id, merchant_category
        HAVING COUNT(*) > 5
        ORDER BY avg_amount DESC;
        ```
        
        This query finds frequent spending categories.
        """
        
        result = extract_sql(sql_input)
        
        assert "SELECT" in result
        assert "user_id" in result
        assert "merchant_category" in result
        assert "GROUP BY" in result
        assert "HAVING" in result
        assert "<think>" not in result
        assert "```" not in result
        assert "This query finds" not in result
    
    def test_extract_sql_edge_cases(self):
        """Test SQL extraction edge cases"""
        # Empty input
        assert extract_sql("") == ""
        
        # Whitespace only
        assert extract_sql("   \n\t   ") == ""
        
        # No SQL content
        result = extract_sql("This is just text without SQL")
        assert result == "This is just text without SQL"
        
        # Multiple code blocks (should take first SQL block)
        multi_block = """
        ```sql
        SELECT * FROM users;
        ```
        Some text
        ```sql
        SELECT * FROM transactions;
        ```
        """
        result = extract_sql(multi_block)
        assert "SELECT * FROM users" in result
    
    def test_extract_sql_case_insensitive(self):
        """Test case insensitive SQL extraction"""
        sql_input = """
        ```SQL
        select * from TRANSACTIONS where AMOUNT > 100;
        ```
        """
        
        result = extract_sql(sql_input)
        
        assert "select * from TRANSACTIONS" in result
        assert "```" not in result


class TestGetLLMClient:
    """Test LLM client selection utility"""
    
    @patch.dict(os.environ, {"LLM_PROVIDER": "openai"})
    def test_get_openai_client(self):
        """Test getting OpenAI client"""
        with patch('agents.utils.LLMClient') as mock_llm:
            mock_instance = mock_llm.return_value
            
            client = get_llm_client()
            
            mock_llm.assert_called_once()
            assert client == mock_instance
    
    @patch.dict(os.environ, {"LLM_PROVIDER": "vertexai"})
    def test_get_vertexai_client(self):
        """Test getting VertexAI client"""
        with patch('agents.utils.VertexAIClient') as mock_vertex:
            mock_instance = mock_vertex.return_value
            
            client = get_llm_client()
            
            mock_vertex.assert_called_once()
            assert client == mock_instance
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_default_client(self):
        """Test getting default client when no provider set"""
        with patch('agents.utils.LLMClient') as mock_llm:
            mock_instance = mock_llm.return_value
            
            client = get_llm_client()
            
            mock_llm.assert_called_once()
            assert client == mock_instance
    
    @patch.dict(os.environ, {"LLM_PROVIDER": "unknown_provider"})
    def test_get_unknown_provider_client(self):
        """Test getting client with unknown provider (should default to OpenAI)"""
        with patch('agents.utils.LLMClient') as mock_llm:
            mock_instance = mock_llm.return_value
            
            client = get_llm_client()
            
            mock_llm.assert_called_once()
            assert client == mock_instance


class TestUtilityRobustness:
    """Test utility function robustness"""
    
    def test_extract_sql_malformed_code_blocks(self):
        """Test handling of malformed code blocks"""
        malformed_inputs = [
            "```sql SELECT * FROM transactions",  # Missing closing ```
            "SELECT * FROM transactions ```",      # Missing opening ```
            "```\nSELECT * FROM transactions\n```", # No language specified
            "```python\nSELECT * FROM transactions\n```", # Wrong language
        ]
        
        for malformed_input in malformed_inputs:
            result = extract_sql(malformed_input)
            # Should handle gracefully and return some result
            assert isinstance(result, str)
    
    def test_extract_response_special_characters(self):
        """Test response extraction with special characters"""
        special_response = "Response with émojis 🚀 and spëcial çharacters ñoño"
        result = extract_response(special_response)
        
        assert result == special_response.strip()
    
    def test_utility_functions_with_none_input(self):
        """Test utility functions with None input"""
        # These should handle None gracefully or raise appropriate errors
        try:
            extract_response(None)
        except (TypeError, AttributeError):
            pass  # Expected behavior
        
        try:
            extract_sql(None)
        except (TypeError, AttributeError):
            pass  # Expected behavior


if __name__ == "__main__":
    pytest.main([__file__])
