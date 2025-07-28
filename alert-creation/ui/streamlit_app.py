import json
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database_utils import get_latest_transaction_for_user, test_database_connection, get_user_transactions_count
    DATABASE_AVAILABLE = True
except ImportError as e:
    st.warning(f"Database utilities not available: {e}")
    DATABASE_AVAILABLE = False

st.set_page_config(page_title="Smart Credit Alerts", layout="wide")
st.title("🚨 Smart Credit Card Alert System")

st.markdown("""
This system allows you to:
1. **Validate Alert Rules** - Test your natural language rules with dummy data
2. **Generate Alerts** - Test rules against real transaction data to see if alerts trigger
""")

st.divider()

# === Natural Language Rule Submission ===
st.subheader("🗣️ Define Custom Natural Language Alert Rule")
default_transaction = {
    "user_id": "7bf1a252-9872-4f70-89c0-fc1a35c2a89f",
    "transaction_date": "2024-01-15T19:30:00",
    "credit_card_num": "1234-5678-9101-1121",
    "amount": 125.50,
    "currency": "USD",
    "description": "Dinner at restaurant",
    "merchant_name": "The Cheesecake Factory",
    "merchant_category": "dining",
    "merchant_city": "New York",
    "merchant_state": "NY",
    "merchant_country": "US",
    "merchant_latitude": 40.7128,
    "merchant_longitude": -74.0060,
    "merchant_zipcode": 10001,
    "trans_num": "txn_001",
    "authorization_code": "AUTH123456",
    "reference_number": "REF789012",
    "first_name": "Michael",
    "last_name": "Johnson"
}
# User ID input
user_id = st.text_input(
    "👤 User ID:", 
    "7bf1a252-9872-4f70-89c0-fc1a35c2a89f",
    help="Enter the user ID to fetch their latest transaction from the database"
)

# Rule input
custom_rule = st.text_input(
    "💬 Natural Language Alert Rule:", 
    value=st.session_state.get('selected_rule', "Alert me when I spend more than $100 on dining"),
    help="Examples: 'Alert me for gas station purchases', 'Alert me when I spend more than $50 on dining'",
    key="rule_input"
)

st.markdown("---")

# === Rule Validation Section ===
st.subheader("1️⃣ Validate Alert Rule")
st.markdown("Test your rule structure and logic with the user's latest transaction from the database")

# Database status check
if DATABASE_AVAILABLE:
    db_status = test_database_connection() if 'test_database_connection' in globals() else False
    if db_status:
        st.success("✅ Database connection available")
        
        # Show user's transaction count
        if user_id.strip():
            try:
                txn_count = get_user_transactions_count(user_id.strip())
                st.info(f"📊 User has {txn_count} transactions in the database")
            except Exception as e:
                st.warning(f"Could not get transaction count: {e}")
    else:
        st.error("❌ Database connection failed")
else:
    st.error("❌ Database utilities not available")

col1, col2 = st.columns([1, 3])

with col1:
    if st.button("🔍 Validate Rule", type="secondary", use_container_width=True):
        if not custom_rule.strip():
            st.error("Please enter an alert rule first!")
        elif not user_id.strip():
            st.error("Please enter a user ID!")
        elif not DATABASE_AVAILABLE:
            st.error("Database connection not available. Using default transaction data.")
            # Fallback to default transaction
            transaction_data = default_transaction
            
            try:
                with st.spinner("Validating rule with default data..."):
                    res = requests.post(
                        "http://localhost:8000/alert-rules/validate", 
                        json={"rule": custom_rule, "transaction": transaction_data}
                    )
                    
                if res.status_code == 200:
                    result = res.json()
                    if result["status"] == "valid":
                        st.success("✅ Rule is valid!")
                        st.info("ℹ️ Validated using default transaction data")
                        with st.expander("View validation details"):
                            st.json(result)
                    elif result["status"] == "invalid":
                        st.warning("⚠️ Rule could not be parsed")
                        st.error(result.get("message", "Unknown validation error"))
                    else:
                        st.error("❌ Validation failed")
                        st.error(result.get("message", "Unknown error"))
                else:
                    st.error(f"API Error: {res.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to API server. Make sure it's running on localhost:8000")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
        else:
            try:
                with st.spinner("Fetching latest transaction from database..."):
                    # Get latest transaction from database
                    latest_transaction = get_latest_transaction_for_user(user_id.strip())
                    
                if not latest_transaction:
                    st.error(f"❌ No transactions found for user {user_id}")
                    st.stop()
                    
                # Display transaction info
                st.info(f"📄 Using transaction: {latest_transaction.get('trans_num')} - ${latest_transaction.get('amount')} at {latest_transaction.get('merchant_name')}")
                
                with st.spinner("Validating rule..."):
                    res = requests.post(
                        "http://localhost:8000/alert-rules/validate", 
                        json={"rule": custom_rule, "transaction": latest_transaction}
                    )
                    
                if res.status_code == 200:
                    result = res.json()
                    if result["status"] == "valid":
                        st.success("✅ Rule is valid!")
                        with st.expander("View validation details"):
                            st.json(result)
                    elif result["status"] == "invalid":
                        st.warning("⚠️ Rule could not be parsed")
                        st.error(result.get("message", "Unknown validation error"))
                    else:
                        st.error("❌ Validation failed")
                        st.error(result.get("message", "Unknown error"))
                else:
                    st.error(f"API Error: {res.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to API server. Make sure it's running on localhost:8000")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")

with col2:
    if 'result' in locals() and result.get("status") == "valid":
        st.info("✅ Rule validation successful! You can now test it with transaction data below.")
    else:
        st.info("💡 Validate your rule first to check if it can be parsed correctly.")

st.markdown("---")

# === Alert Generation Section ===
st.subheader("2️⃣ Generate Alert with Transaction Data")
st.markdown("Test your rule against actual transaction data to see if alerts are triggered")

# Transaction input
st.subheader("🧾 Transaction Data")
transaction_input = st.text_area(
    "Transaction JSON (edit as needed):",
    value=json.dumps(default_transaction, indent=2),
    height=300,
    help="Modify the transaction data to test different scenarios"
)

col3, col4 = st.columns([1, 3])

with col3:
    if st.button("🚨 Generate Alert", type="primary", use_container_width=True):
        if not custom_rule.strip():
            st.error("Please enter an alert rule first!")
        elif not transaction_input.strip():
            st.error("Please provide transaction data!")
        else:
            try:
                # Parse transaction JSON
                transaction_data = json.loads(transaction_input)
                
                with st.spinner("Generating alert..."):
                    res = requests.post(
                        "http://localhost:8000/alert-rules/generate", 
                        json={
                            "rule": custom_rule,
                            "transaction": transaction_data
                        }
                    )
                    
                if res.status_code == 200:
                    result = res.json()
                    
                    if result["status"] == "triggered":
                        st.success("🚨 Alert Triggered!")
                        
                        # Display alert details
                        alert = result.get("alert", {})
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.metric("Amount", f"${alert.get('amount', 'N/A')}")
                            st.metric("Merchant", alert.get('merchant', 'N/A'))
                            
                        with col_b:
                            st.metric("Alert Type", alert.get('type', 'N/A'))
                            st.metric("Severity", alert.get('severity', 'N/A'))
                            
                        st.text_area("Alert Message:", alert.get('description', 'No description'), height=100)
                        
                        with st.expander("View full alert details"):
                            st.json(result)
                            
                    elif result["status"] == "not_triggered":
                        st.info("ℹ️ Rule evaluated but no alert was triggered")
                        st.markdown(f"**Transaction ID:** {result.get('transaction_id', 'N/A')}")
                        
                        with st.expander("View evaluation details"):
                            st.json(result)
                            
                    else:
                        st.error("❌ Alert generation failed")
                        st.error(result.get("message", "Unknown error"))
                        
                else:
                    st.error(f"API Error: {res.status_code}")
                    
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON in transaction data. Please check the format.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to API server. Make sure it's running on localhost:8000")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")

with col4:
    st.info("💡 Click 'Generate Alert' to test your rule against the transaction data. Modify the transaction amount, merchant, or category to test different scenarios.")

# === Example Rules Section ===
st.markdown("---")
st.subheader("💡 Example Alert Rules")

example_rules = [
    "Alert me when I spend more than $100",
    "Alert me for any dining purchases over $50", 
    "Alert me for gas station purchases",
    "Alert me for transactions outside California",
    "Alert me when I make more than 3 purchases in a day",
    "Alert me for any purchase at Amazon",
    "Alert me for international transactions"
]

st.markdown("**Try these example rules:**")
cols = st.columns(2)

for i, rule in enumerate(example_rules):
    col = cols[i % 2]
    with col:
        if st.button(f"📝 {rule}", key=f"example_{i}"):
            st.session_state.rule_input = rule
            st.rerun()

# === API Status ===
st.markdown("---")
st.subheader("🔧 API Status")

try:
    health_res = requests.get("http://localhost:8000/docs", timeout=5)
    if health_res.status_code == 200:
        st.success("✅ API server is running")
        st.markdown("API Documentation: http://localhost:8000/docs")
    else:
        st.warning(f"⚠️ API server responded with status {health_res.status_code}")
except:
    st.error("❌ API server is not responding. Start it with: `uvicorn main:app --reload`")
