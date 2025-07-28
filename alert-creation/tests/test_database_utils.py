"""
Test cases for database utility functions
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.database_utils import (
    get_database_connection, 
    get_latest_transaction_for_user, 
    get_user_transactions_count,
    test_database_connection
)


class TestDatabaseConnection:
    """Test database connection functionality"""
    
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost:5432/test"})
    @patch('database_utils.psycopg2.connect')
    def test_get_database_connection_success(self, mock_connect):
        """Test successful database connection"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        result = get_database_connection()
        
        assert result == mock_conn
        mock_connect.assert_called_once_with("postgresql://test:test@localhost:5432/test")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_database_connection_no_url(self):
        """Test database connection without DATABASE_URL"""
        result = get_database_connection()
        
        assert result is None
    
    @patch.dict(os.environ, {"DATABASE_URL": "invalid_url"})
    @patch('database_utils.psycopg2.connect')
    def test_get_database_connection_failure(self, mock_connect):
        """Test database connection failure"""
        mock_connect.side_effect = Exception("Connection failed")
        
        result = get_database_connection()
        
        assert result is None


class TestGetLatestTransaction:
    """Test latest transaction retrieval"""
    
    @patch('database_utils.get_database_connection')
    def test_get_latest_transaction_success(self, mock_get_conn):
        """Test successful transaction retrieval"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Mock transaction data
        mock_transaction_data = {
            'id': 'txn_123',
            'trans_num': 'TXN001',
            'user_id': 'user_123',
            'credit_card_num': '1234',
            'first_name': 'John',
            'last_name': 'Doe',
            'amount': 89.99,
            'currency': 'USD',
            'description': 'Test transaction',
            'merchant_name': 'Test Store',
            'merchant_category': 'retail',
            'transaction_date': '2024-01-15T10:30:00',
            'transaction_type': 'PURCHASE',
            'merchant_latitude': 37.7749,
            'merchant_longitude': -122.4194,
            'merchant_city': 'San Francisco',
            'merchant_state': 'CA',
            'merchant_country': 'US',
            'status': 'APPROVED',
            'authorization_code': 'AUTH123',
            'reference_number': 'REF456',
            'merchantZipcode': 94102
        }
        
        mock_cursor.fetchone.return_value = mock_transaction_data
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = get_latest_transaction_for_user('user_123')
        
        assert result is not None
        assert result['user_id'] == 'user_123'
        assert result['amount'] == 89.99
        assert result['merchant_name'] == 'Test Store'
        assert result['merchant_zipcode'] == 94102
        
        # Verify cursor was called with correct query
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0]
        assert 'user_123' in args[1]
    
    @patch('database_utils.get_database_connection')
    def test_get_latest_transaction_not_found(self, mock_get_conn):
        """Test transaction retrieval when no transactions exist"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = get_latest_transaction_for_user('nonexistent_user')
        
        assert result is None
    
    @patch('database_utils.get_database_connection')
    def test_get_latest_transaction_no_connection(self, mock_get_conn):
        """Test transaction retrieval with no database connection"""
        mock_get_conn.return_value = None
        
        result = get_latest_transaction_for_user('user_123')
        
        assert result is None
    
    @patch('database_utils.get_database_connection')
    def test_get_latest_transaction_database_error(self, mock_get_conn):
        """Test transaction retrieval with database error"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = get_latest_transaction_for_user('user_123')
        
        assert result is None


class TestGetUserTransactionsCount:
    """Test user transaction count functionality"""
    
    @patch('database_utils.get_database_connection')
    def test_get_user_transactions_count_success(self, mock_get_conn):
        """Test successful transaction count retrieval"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (5,)  # 5 transactions
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = get_user_transactions_count('user_123')
        
        assert result == 5
        mock_cursor.execute.assert_called_once()
    
    @patch('database_utils.get_database_connection')
    def test_get_user_transactions_count_zero(self, mock_get_conn):
        """Test transaction count with zero transactions"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (0,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = get_user_transactions_count('user_123')
        
        assert result == 0
    
    @patch('database_utils.get_database_connection')
    def test_get_user_transactions_count_no_connection(self, mock_get_conn):
        """Test transaction count with no database connection"""
        mock_get_conn.return_value = None
        
        result = get_user_transactions_count('user_123')
        
        assert result == 0


class TestDatabaseConnectionTest:
    """Test database connection testing functionality"""
    
    @patch('database_utils.get_database_connection')
    def test_database_connection_test_success(self, mock_get_conn):
        """Test successful database connection test"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = test_database_connection()
        
        assert result is True
        mock_cursor.execute.assert_called_once_with('SELECT 1')
    
    @patch('database_utils.get_database_connection')
    def test_database_connection_test_failure(self, mock_get_conn):
        """Test failed database connection test"""
        mock_get_conn.return_value = None
        
        result = test_database_connection()
        
        assert result is False
    
    @patch('database_utils.get_database_connection')
    def test_database_connection_test_error(self, mock_get_conn):
        """Test database connection test with execution error"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Query failed")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = test_database_connection()
        
        assert result is False


class TestTransactionDataFormatting:
    """Test transaction data formatting"""
    
    @patch('database_utils.get_database_connection')
    def test_transaction_data_types(self, mock_get_conn):
        """Test that transaction data is properly formatted"""
        from datetime import datetime
        
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Mock transaction with datetime object
        mock_transaction_data = {
            'amount': '89.99',  # String that should be converted to float
            'merchant_zipcode': '94102',  # String that should be converted to int
            'transaction_date': datetime(2024, 1, 15, 10, 30, 0),  # datetime object
            'currency': None,  # Should get default value
            'merchant_country': None,  # Should get default value
            'user_id': 'user_123',
            'trans_num': 'TXN001'
        }
        
        mock_cursor.fetchone.return_value = mock_transaction_data
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = get_latest_transaction_for_user('user_123')
        
        assert result is not None
        assert isinstance(result['amount'], float)
        assert result['amount'] == 89.99
        assert isinstance(result['merchant_zipcode'], int)
        assert result['merchant_zipcode'] == 94102
        assert isinstance(result['transaction_date'], str)
        assert result['currency'] == 'USD'  # Default value
        assert result['merchant_country'] == 'US'  # Default value


if __name__ == "__main__":
    pytest.main([__file__])
