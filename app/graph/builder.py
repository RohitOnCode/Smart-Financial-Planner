
from langgraph.graph import StateGraph, END
from app.graph.state import ResearchState
from app.agents import researcher, curator, fact_checker, writer

def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("researcher", researcher.node)
    g.add_node("curator", curator.node)
    g.add_node("fact_checker", fact_checker.node)
    g.add_node("writer", writer.node)
    g.set_entry_point("researcher")
    g.add_edge("researcher","curator")
    g.add_edge("curator","fact_checker")
    g.add_edge("fact_checker","writer")
    g.add_edge("writer", END)
    return g.compile()
