# agent_logic.py
import re
import json
from typing import TypedDict
from langgraph.graph import StateGraph
from datetime import datetime

from .gemini_chain import run_gemini_chain  # ✅ Imported cleanly
from dotenv import load_dotenv
import os

load_dotenv()


# Define the LangGraph state
class AgentState(TypedDict):
    input: str
    result: dict

# Define LangGraph node
def parse_node(state: AgentState) -> AgentState:
    user_text = state["input"]
    try:
        output = run_gemini_chain(user_text)
        json_match = re.search(r"\{.*?\}", output, re.DOTALL)
        if json_match:
            return {"result": json.loads(json_match.group())}
        else:
            return {"result": {"error": "No JSON found"}}
    except Exception as e:
        return {"result": {"error": str(e)}}

# Build LangGraph flow
def build_parser_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse", parse_node)
    graph.set_entry_point("parse")
    graph.set_finish_point("parse")
    return graph.compile()

# Public function for use in Streamlit or API
def run_langgraph_agent(user_input: str) -> dict:
    graph = build_parser_graph()
    result = graph.invoke({"input": user_input})
    return result.get("result", {"error": "No result returned"})
