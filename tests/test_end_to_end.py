
import os
from app.graph.builder import build_graph

def test_end_to_end():
    g = build_graph()
    res = g.invoke({"query":"NVIDIA data center outlook 2025", "ticker":"NVDA"})
    assert res.get("report_html") and os.path.exists(res["report_html"])
