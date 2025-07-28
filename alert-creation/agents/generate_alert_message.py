
from langchain_core.tools import tool
from .utils import extract_response, get_llm_client
@tool
def generate_alert_message(transaction: dict, query_result: str, alert_text: str, alert_type: str) -> str:
    """
    Generate a user-facing alert message based on alert type.
    """
    first = transaction.get("first", "")
    last = transaction.get("last", "")
    user = f"{first} {last}".strip()
    amount = transaction.get("amt")
    category = transaction.get("category", "")
    merchant = transaction.get("merchant", "")
    city = transaction.get("city", "")
    state = transaction.get("state", "")

    if alert_type == "spending":
        prompt = f"""
The user {user} triggered an alert for excessive spending.

- Alert: "{alert_text}"
- Transaction amount: ${amount}
- Category: {category}
- Merchant: {merchant}
- SQL result: {query_result}

Write a 1-2 sentence friendly alert message explaining why the spending alert was triggered.
"""
    elif alert_type == "location":
        prompt = f"""
The user {user} triggered an alert for a location-based transaction.

- Alert: "{alert_text}"
- Location: {city}, {state}
- Merchant: {merchant}
- SQL result: {query_result}

Write a 1-2 sentence alert message explaining why the location alert was triggered.
"""
    elif alert_type == "merchant":
        prompt = f"""
The user {user} triggered an alert related to a new or repeated merchant.

- Alert: "{alert_text}"
- Merchant: {merchant}
- SQL result: {query_result}

Write a 1-2 sentence friendly alert message explaining why this merchant alert was triggered.
"""
    else:
        prompt = f"""
User: {user}
Alert: {alert_text}
Transaction: ${amount} at {merchant}
SQL Result: {query_result}

Write a friendly alert message for a general transaction alert.
"""

    client = get_llm_client()
    response = client.invoke(prompt)
    return extract_response(response.content)
