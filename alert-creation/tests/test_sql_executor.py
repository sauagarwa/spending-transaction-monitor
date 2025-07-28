"""
Test cases for SQL executor functionality
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sql_executor import execute_sql


class TestSQLExecutor:
    """Test SQL execution functionality"""
    
    @patch('agents.sql_executor.get_connection')
    def test_execute_sql_success(self, mock_get_connection):
        """Test successful SQL execution"""
        # Mock cursor and connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("John", "Doe", 100.50), ("Jane", "Smith", 75.25)]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("SELECT first_name, last_name, amount FROM transactions LIMIT 2")
        
        # Verify cursor was called correctly
        mock_cursor.execute.assert_called_once_with("SELECT first_name, last_name, amount FROM transactions LIMIT 2")
        mock_cursor.fetchall.assert_called_once()
        
        # Check result format
        assert isinstance(result, str)
        assert "John" in result
        assert "Doe" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_execute_sql_empty_result(self, mock_get_connection):
        """Test SQL execution with empty result set"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("SELECT * FROM transactions WHERE amount > 10000")
        
        assert result == "[]"
    
    @patch('agents.sql_executor.get_connection')
    def test_execute_sql_error(self, mock_get_connection):
        """Test SQL execution with database error"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Table 'transactions' doesn't exist")
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("SELECT * FROM non_existent_table")
        
        assert "SQL Error:" in result
        assert "doesn't exist" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_execute_sql_syntax_error(self, mock_get_connection):
        """Test SQL execution with syntax error"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("syntax error at or near 'SELCT'")
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("SELCT * FROM transactions")  # Typo in SELECT
        
        assert "SQL Error:" in result
        assert "syntax error" in result
    
    def test_execute_sql_parameter_validation(self):
        """Test SQL parameter validation"""
        # Test with None parameter
        result = execute_sql(None)
        assert "SQL Error:" in result
        
        # Test with empty string
        result = execute_sql("")
        assert "SQL Error:" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_execute_sql_different_data_types(self, mock_get_connection):
        """Test SQL execution with different data types"""
        mock_conn = Mock()
        mock_cursor = Mock()
        # Mix of string, int, float, and None values
        mock_cursor.fetchall.return_value = [
            ("Alice", 25, 123.45, None),
            ("Bob", 30, 67.89, "2024-01-15")
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("SELECT name, age, amount, date FROM test_table")
        
        assert "Alice" in result
        assert "25" in result
        assert "123.45" in result
        assert "None" in result or "null" in result.lower()


class TestSQLQueries:
    """Test specific SQL query patterns used in alert system"""
    
    @patch('agents.sql_executor.get_connection')
    def test_amount_threshold_query(self, mock_get_connection):
        """Test amount threshold alert query"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("txn_001", 150.00, "Expensive Restaurant")]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        query = """
        SELECT trans_num, amount, merchant_name 
        FROM transactions 
        WHERE user_id = 'user123' AND amount > 100
        """
        
        result = execute_sql(query)
        
        mock_cursor.execute.assert_called_once_with(query)
        assert "150.0" in result
        assert "Expensive Restaurant" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_category_based_query(self, mock_get_connection):
        """Test category-based alert query"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("txn_002", "dining", "Restaurant ABC", 45.50),
            ("txn_003", "dining", "Fast Food Place", 12.99)
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        query = """
        SELECT trans_num, merchant_category, merchant_name, amount 
        FROM transactions 
        WHERE user_id = 'user123' AND merchant_category = 'dining'
        """
        
        result = execute_sql(query)
        
        assert "dining" in result
        assert "Restaurant ABC" in result
        assert "45.5" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_time_based_query(self, mock_get_connection):
        """Test time-based alert query"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("txn_004", "2024-01-15 14:30:00", 89.99)]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        query = """
        SELECT trans_num, transaction_date, amount 
        FROM transactions 
        WHERE user_id = 'user123' 
        AND transaction_date >= '2024-01-15 00:00:00'
        """
        
        result = execute_sql(query)
        
        assert "2024-01-15" in result
        assert "89.99" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_aggregation_query(self, mock_get_connection):
        """Test aggregation queries for spending analysis"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [(3, 245.48)]  # count, sum
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        query = """
        SELECT COUNT(*), SUM(amount) 
        FROM transactions 
        WHERE user_id = 'user123' 
        AND merchant_category = 'dining'
        AND transaction_date >= '2024-01-01'
        """
        
        result = execute_sql(query)
        
        assert "3" in result
        assert "245.48" in result


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('agents.sql_executor.get_connection')
    def test_connection_timeout(self, mock_get_connection):
        """Test database connection timeout"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("connection timeout")
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("SELECT * FROM transactions LIMIT 1")
        
        assert "SQL Error:" in result
        assert "timeout" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_permission_error(self, mock_get_connection):
        """Test database permission error"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("permission denied for table transactions")
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("DELETE FROM transactions")
        
        assert "SQL Error:" in result
        assert "permission denied" in result
    
    @patch('agents.sql_executor.get_connection')
    def test_large_result_set(self, mock_get_connection):
        """Test handling of large result sets"""
        mock_conn = Mock()
        mock_cursor = Mock()
        # Simulate large result set
        large_result = [("txn_%d" % i, i * 10.5) for i in range(1000)]
        mock_cursor.fetchall.return_value = large_result
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn
        
        result = execute_sql("SELECT trans_num, amount FROM transactions")
        
        assert isinstance(result, str)
        assert len(result) > 0  # Should handle large results


if __name__ == "__main__":
    pytest.main([__file__])
