
import time, json, ast, os
from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from app.graph.state import ResearchState
from app.agents.summarizer import summarize_docs
from app.agents.tools.tools import build_index, search_index

def _parse(content):
    if isinstance(content, (list, dict)):
        return content
    s=str(content)
    try:
        return json.loads(s)
    except Exception:
        try:
            return ast.literal_eval(s)
        except Exception:
            return s

def node(state: ResearchState) -> ResearchState:
    state.setdefault('trace', []).append({'node':'curator','t': time.time()})
    q = state.get("query",""); docs = state.get("docs",[]) or []
    # ToolNode 1: build_index (with metadata)
    idx_node = ToolNode([build_index])
    res1 = idx_node.invoke({"messages":[AIMessage(content="", tool_calls=[{"name":"build_index","args":{"docs": docs}, "id":"tc_idx","type":"tool_call"}])]})
    idx_msg = res1["messages"][0]
    idx = _parse(idx_msg.content) or {}
    # ToolNode 2: search_index
    selected = docs[:6]
    if isinstance(idx, dict) and idx.get("ok") and idx.get("key"):
        search_node = ToolNode([search_index])
        res2 = search_node.invoke({"messages":[AIMessage(content="", tool_calls=[{"name":"search_index","args":{"key": idx["key"], "query": q, "k": 6}, "id":"tc_s","type":"tool_call"}])]})
        s_msg = res2["messages"][0]
        hits = _parse(s_msg.content) or []
        if isinstance(hits, list) and hits:
            selected = [{"url": (h.get("metadata") or {}).get("url",""), "title": (h.get("metadata") or {}).get("title",""), "text": h.get("text","")} for h in hits]
    state["docs"]=selected
    state["summary"]=summarize_docs(selected, q)
    state.setdefault('trace', []).append({'node':'curator:done','t': time.time(), 'docs': len(selected)})
    return state
