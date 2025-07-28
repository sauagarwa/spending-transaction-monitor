from langchain_core.tools import tool
from .utils import extract_response
from .utils import get_llm_client
@tool
def classify_alert_type(alert_text: str) -> str:
    """
    Classifies an alert into one of:
    - spending
    - location
    - merchant
    """
    print("**** in classify alert type ***")
    prompt = f"""
Classify the following alert into one of the following types:
- spending
- location
- merchant

Alert: "{alert_text}"

Respond with only one word.
"""
    client = get_llm_client()
    response = client.invoke(prompt)
    return extract_response(response.content)

