# app.py
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from agents.alert_parser import parse_alert_to_sql_with_context
from agents.generate_alert_message import generate_alert_message
from agents.classify_alert_type import classify_alert_type
from agents.sql_executor import execute_sql

# Define app state
class AppState(dict):
    transaction: dict
    alert_text: str
    sql_query: str
    query_result: str
    valid_sql: bool

graph = StateGraph(AppState)

# Step 1: Parse alert
graph.add_node("parse_alert", RunnableLambda(lambda state: {
    **state,
    "sql_query": parse_alert_to_sql_with_context({
        "transaction": state["transaction"],
        "alert_text": state["alert_text"]
    })
}))

# Step 2: Execute SQL
graph.add_node("execute_sql", RunnableLambda(lambda state: {
    **state,
    "query_result": execute_sql(state["sql_query"])
}))

def validate_sql(state):
    """Sets alert_triggered to True if query result indicates match."""
    result = state["query_result"]
    try:
        # Naive check: if result has rows and doesn't start with "SQL Error"
        valid_sql = result and not result.startswith("SQL Error")
    except Exception:
        valid_sql = False
    print(" In generate alert ", valid_sql)
    return {
        **state,
        "valid_sql": valid_sql
    }


# Step 2: Create Alert
graph.add_node("validate_sql", RunnableLambda(validate_sql))

# Edges
graph.set_entry_point("parse_alert")
graph.add_edge("parse_alert", "execute_sql")
graph.add_edge("execute_sql", "validate_sql")

app = graph.compile()
