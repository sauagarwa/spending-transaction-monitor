"""
Database utilities for connecting to PostgreSQL and retrieving transaction data
"""
import os
import psycopg2
import psycopg2.extras
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_database_connection():
    """Get PostgreSQL database connection"""
    try:
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            logger.warning("DATABASE_URL not set, cannot connect to database")
            return None
            
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def get_latest_transaction_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the latest transaction for a specific user from the database
    
    Args:
        user_id: The user ID to search for
        
    Returns:
        Dictionary containing transaction data or None if not found
    """
    conn = get_database_connection()
    if not conn:
        return None
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            query = """
            SELECT 
                t.id,
                t.trans_num,
                t."user_id" as user_id,
                t."credit_card_num" as credit_card_num,
                t."first_name" as first_name,
                t."last_name" as last_name,
                t.amount,
                t.currency,
                t.description,
                t."merchant_name" as merchant_name,
                t."merchant_category" as merchant_category,
                t."transaction_date" as transaction_date,
                t."transaction_type" as transaction_type,
                t."merchant_latitude" as merchant_latitude,
                t."merchant_longitude" as merchant_longitude,
                t."merchant_city" as merchant_city,
                t."merchant_state" as merchant_state,
                t."merchant_country" as merchant_country,
                t.status,
                t."authorization_code" as authorization_code,
                t."reference_number" as reference_number,
                t."merchant_zipcode" as merchant_zipcode
            FROM "transactions" t
            WHERE t."user_id" = %s
            ORDER BY t."transaction_date" DESC, t."created_at" DESC
            LIMIT 1
            """
            
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                # Convert RealDictRow to regular dict and format data
                transaction = dict(result)
                
                # Format transaction_date as ISO string if it's a datetime
                if isinstance(transaction.get('transaction_date'), datetime):
                    transaction['transaction_date'] = transaction['transaction_date'].isoformat()
                
                # Ensure numeric fields are properly typed
                transaction['amount'] = float(transaction['amount']) if transaction['amount'] else 0.0
                transaction['merchant_zipcode'] = int(transaction['merchant_zipcode']) if transaction['merchant_zipcode'] else 0
                
                # Set default values for optional fields
                transaction['currency'] = transaction.get('currency') or 'USD'
                transaction['merchant_country'] = transaction.get('merchant_country') or 'US'
                
                logger.info(f"Found latest transaction {transaction['trans_num']} for user {user_id}")
                return transaction
            else:
                logger.warning(f"No transactions found for user {user_id}")
                return None
                
    except Exception as e:
        logger.error(f"Error retrieving transaction for user {user_id}: {e}")
        return None
    finally:
        conn.close()

def get_user_transactions_count(user_id: str) -> int:
    """
    Get the total number of transactions for a user
    
    Args:
        user_id: The user ID to search for
        
    Returns:
        Number of transactions or 0 if error/none found
    """
    conn = get_database_connection()
    if not conn:
        return 0
        
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM "transactions" WHERE "user_id" = %s', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting transactions for user {user_id}: {e}")
        return 0
    finally:
        conn.close()

def test_database_connection() -> bool:
    """
    Test if database connection is working
    
    Returns:
        True if connection successful, False otherwise
    """
    conn = get_database_connection()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            return result[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
    finally:
        conn.close()
