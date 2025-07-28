import re
from .vertexai import VertexAIClient
from .llm import LLMClient
import os
def extract_response(response: str) -> str:
    # Match from SELECT ... until semicolon
    match = re.search(r"(.*)", response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return response.strip()

def extract_sql(sql: str) -> str:
    # 1. Remove <think> blocks if present
    """Clean and normalize LLM SQL output."""
    # Remove reasoning tags
    if "</think>" in sql:
        sql = sql.split("</think>")[-1]

    # Extract from ```sql ... ``` block
    code_block = re.search(r"```sql(.*?)```", sql, re.DOTALL | re.IGNORECASE)
    if code_block:
        sql = code_block.group(1)

    sql = sql.strip()

    # 🔑 Safeguard: if query contains FROM ( but no WITH, wrap it as CTE
    if "FROM (" in sql.upper() and not sql.strip().upper().startswith("WITH"):
        sql = f"WITH subquery AS ({sql}) SELECT * FROM subquery"

    return sql.strip()

def get_llm_client():
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "vertexai":
        return VertexAIClient()
    else:
        return LLMClient()

        