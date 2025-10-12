
import time, json, ast, os
from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from app.graph.state import ResearchState
from app.agents.tools.tools import extract_claims_tool, verify_claims_tool
from app.config import MIN_EVIDENCE_OVERLAP

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
    state.setdefault('trace', []).append({'node':'fact_checker','t': time.time()})
    q = state.get("query",""); docs = state.get("docs",[]) or []; sm = state.get("summary","")
    # ToolNode 1: extract_claims_tool
    claims_node = ToolNode([extract_claims_tool])
    res1 = claims_node.invoke({"messages":[AIMessage(content="", tool_calls=[{"name":"extract_claims_tool","args":{"summary": sm, "topic": q, "n": 6}, "id":"tc_c","type":"tool_call"}])]})
    c_msg = res1["messages"][0]
    claims = _parse(c_msg.content) or []
    # ToolNode 2: verify_claims_tool (respect env overlap)
    verify_node = ToolNode([verify_claims_tool])
    res2 = verify_node.invoke({"messages":[AIMessage(content="", tool_calls=[{"name":"verify_claims_tool","args":{"claims": claims, "sources": docs, "min_overlap": int(os.getenv('MIN_EVIDENCE_OVERLAP', str(MIN_EVIDENCE_OVERLAP)))},"id":"tc_v","type":"tool_call"}])]})
    v_msg = res2["messages"][0]
    checked = _parse(v_msg.content) or []
    state["claims"]=claims if isinstance(claims, list) else []
    state["checked_claims"]=checked if isinstance(checked, list) else []
    state.setdefault('trace', []).append({'node':'fact_checker:done','t': time.time(), 'claims': len(state["checked_claims"])})
    return state
