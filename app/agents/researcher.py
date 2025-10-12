
import time, json, ast
from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from app.graph.state import ResearchState
from app.agents.tools.tools import web_search, http_fetch

def _parse_tool_content(content):
    if isinstance(content, (list, dict)):
        return content
    s = str(content)
    try:
        return json.loads(s)
    except Exception:
        try:
            return ast.literal_eval(s)
        except Exception:
            return s

def node(state: ResearchState) -> ResearchState:
    state.setdefault('trace', []).append({'node':'researcher','t': time.time()})
    q = state.get("query") or state.get("ticker") or ""
    # ToolNode 1: web_search
    search_node = ToolNode([web_search])
    msg1 = AIMessage(content="", tool_calls=[{"name":"web_search","args":{"query": q, "max_results": 10}, "id":"tc_search","type":"tool_call"}])
    res1 = search_node.invoke({"messages":[msg1]})
    hits_msg = res1["messages"][0]
    hits = _parse_tool_content(hits_msg.content) or []

    # ToolNode 2: http_fetch (top 6)
    fetch_node = ToolNode([http_fetch])
    tool_calls = []
    for h in (hits if isinstance(hits, list) else [] )[:6]:
        url = h.get("link") or h.get("url") or ""
        if not url: continue
        tool_calls.append({"name":"http_fetch","args":{"url": url, "timeout": 15}, "id": f"tc_fetch_{len(tool_calls)}", "type":"tool_call"})
    docs = []
    if tool_calls:
        res2 = fetch_node.invoke({"messages":[AIMessage(content="", tool_calls=tool_calls)]})
        for m in res2["messages"]:
            d = _parse_tool_content(m.content)
            if isinstance(d, dict):
                docs.append({"url": d.get("url",""), "title": d.get("title",""), "text": d.get("text","")})
    else:
        docs=[{"url": (hits[0].get("link") if hits else ""), "title": (hits[0].get("title") if hits else ""), "text": (hits[0].get("snippet") if hits else "")}]
    state["web_results"]=hits if isinstance(hits, list) else []
    state["docs"]=docs
    state.setdefault('trace', []).append({'node':'researcher:done','t': time.time(), 'docs': len(state.get("docs",[]))})
    return state
