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
    alert_triggered: bool
    alert_message: str
    alert_type: str

graph = StateGraph(AppState)

def generate_alert(state):
    """Sets alert_triggered to True if query result indicates match."""
    result = state["query_result"]
    try:
        # Naive check: if result has rows and doesn't start with "SQL Error"
        alert_triggered = result and not result.startswith("SQL Error") and result != "[]"
    except Exception:
        alert_triggered = False
    print(" In generate alert ", alert_triggered)
    return {
        **state,
        "alert_triggered": alert_triggered
    }

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

# Step 2: Create Alert
graph.add_node("create_alert", RunnableLambda(generate_alert))

graph.add_node("classify_type", RunnableLambda(lambda state: {
    **state,
    "alert_type": classify_alert_type(state["alert_text"])
}))

graph.add_node("generate_alert_message", RunnableLambda(lambda state: {
    **state,
    "alert_message": generate_alert_message({
        "transaction": state["transaction"],
        "query_result": state["query_result"],
        "alert_text": state["alert_text"],
        "alert_type":state["alert_type"]
    }) if state.get("alert_triggered") else ""
}))


# Edges
graph.set_entry_point("parse_alert")
graph.add_edge("parse_alert", "execute_sql")
graph.add_edge("execute_sql", "create_alert")
graph.add_edge("create_alert", "classify_type")
graph.add_edge("classify_type", "generate_alert_message")



app = graph.compile()
