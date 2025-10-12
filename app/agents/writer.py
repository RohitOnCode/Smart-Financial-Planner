
import os, time, json, ast, hashlib
from typing import Optional, List, Dict, Any
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from app.graph.state import ResearchState
from app.agents.tools.tools import extract_kpis_from_page, kpi_web_fallback, price_projection_chart
from app.config import OUTPUTS_DIR

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

def _render_sources_json(q: str, docs: List[Dict[str, Any]]):
    items=[]
    for d in docs[:12]:
        url = d.get('url',''); title = d.get('title','') or url
        text = d.get('text','') or ''
        items.append({"url":url, "title":title, "text": text[:1200]})
    h = hashlib.sha1((q+str(time.time())).encode()).hexdigest()[:10]
    path = os.path.join(OUTPUTS_DIR, f"sources_{h}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"sources": items}, f, indent=2)
    return f"/outputs/{os.path.basename(path)}"

def render_report(query: str, ticker: Optional[str], summary: str, kpi: Dict[str, Any], checked: List[Dict[str, Any]], sources_url: str, proj5: Optional[str], proj10: Optional[str]) -> str:
    rows = []
    gm = kpi.get('gross_margin'); om = kpi.get('operating_margin')
    def fmt(v):
        if v is None: return "-"
        try: return f"{float(v):.2f}"
        except Exception: return str(v)
    rows.append(("P/E (ttm)", fmt(kpi.get("p_e_ratio"))))
    rows.append(("P/S (ttm)", fmt(kpi.get("p_s_ratio"))))
    rows.append(("Gross Margin", f"{gm*100:.1f}%" if gm is not None else "-"))
    rows.append(("Operating Margin", f"{om*100:.1f}%" if om is not None else "-"))
    kpi_rows = "".join([f"<tr><td class='pr-3 py-1 opacity-80'>{k}</td><td class='py-1'>{v}</td></tr>" for k,v in rows])

    claims_rows = []
    for c in checked:
        verdict = "✅ True" if c.get("verdict") else "⚠️ Unverified"
        ev = c.get("evidence_url") or ""
        claims_rows.append(f"<tr><td>{c.get('claim')}</td><td>{verdict}</td><td><a href='{ev}' target='_blank'>{ev}</a></td></tr>")
    claims_table = "\n".join(claims_rows) or "<tr><td colspan='3' class='opacity-60'>No claims extracted.</td></tr>"

    proj_html = ""
    if proj5 or proj10:
        proj_html = "<div class='grid grid-cols-1 md:grid-cols-2 gap-4'>"
        if proj5: proj_html += f"<img src='{proj5}' class='w-full rounded border border-gray-800'/>"
        if proj10: proj_html += f"<img src='{proj10}' class='w-full rounded border border-gray-800'/>"
        proj_html += "</div>"

    script_js = """
    async function loadSources(){
      const el = document.getElementById('sources');
      if(!el.dataset.loaded){
        const r = await fetch('__SRC__');
        const d = await r.json();
        el.innerHTML = (d.sources || [])
          .map(s => `<div class='mb-3'>
                       <div class='font-semibold'>${s.title}
                         <span class='text-xs opacity-60'> ${s.url}</span>
                       </div>
                       <div class='text-sm opacity-80'>${(s.text || '').slice(0,600)}</div>
                     </div>`)
          .join('');
        el.dataset.loaded = '1';
        el.classList.remove('hidden');
      }
    }
    """.replace("__SRC__", sources_url)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/>
  <title>Research Report — Smart Financial Planner</title>
  <link href='https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css' rel='stylesheet'>
  <style>
    body{{background:#0b0f19;color:#e5e7eb}}
    .card{{background:#111827;border:1px solid #1f2937;border-radius:14px;padding:20px}}
    a{{color:#60a5fa}}
  </style>
  <script>{script_js}</script>
</head>
<body class='p-6'>
  <div class='max-w-6xl mx-auto space-y-6'>
    <header class='flex items-center justify-between'>
      <h1 class='text-2xl font-bold'>Smart Financial Planner</h1>
      <span class='text-sm opacity-70'>{time.strftime("%Y-%m-%d %H:%M:%S")}</span>
    </header>
    <section class='card'>
      <div class='flex items-center justify-between'>
        <div><div class='text-xl font-semibold'>Topic</div><p class='opacity-80'><b>Query:</b> {query} &nbsp; | &nbsp; <b>Ticker:</b> {ticker or '-'}</p></div>
        <button onclick='loadSources()' class='px-3 py-1 rounded bg-gray-800 border border-gray-700'>Show Sources</button>
      </div>
      <div id='sources' class='hidden mt-3 p-3 border border-gray-800 rounded bg-gray-900 text-sm' data-loaded=''></div>
    </section>
    <section class='card'>
      <h2 class='text-xl font-semibold mb-2'>Curated Summary</h2>
      <div class='prose prose-invert'>{summary.replace("\n","<br/>")}</div>
    </section>
    <section class='card'>
      <h2 class='text-xl font-semibold mb-2'>KPI Table (web + yfinance fallback)</h2>
      <table class='text-sm'><tbody>{kpi_rows}</tbody></table>
    </section>
    <section class='card'>
      <h2 class='text-xl font-semibold mb-2'>Price Projection (5Y & 10Y)</h2>
      {proj_html or "<p class='opacity-60'>Projection not available.</p>"}
    </section>
    <section class='card'>
      <h2 class='text-xl font-semibold mb-2'>Checked Claims</h2>
      <div class='overflow-x-auto'>
        <table class='min-w-full text-sm'>
          <thead><tr><th class='text-left'>Claim</th><th class='text-left'>Verdict</th><th class='text-left'>Evidence</th></tr></thead>
          <tbody>{claims_table}</tbody>
        </table>
      </div>
    </section>
  </div>
</body></html>"""
    return html

def node(state: ResearchState) -> ResearchState:
    q = state.get("query","" ); t = state.get("ticker")
    docs = state.get("docs",[])
    # KPIs
    kpi_node = ToolNode([extract_kpis_from_page, kpi_web_fallback])
    agg = "\n\n".join([d.get("text","")[:6000] for d in docs])[:24000]
    res1 = kpi_node.invoke({"messages":[AIMessage(content="", tool_calls=[{"name":"extract_kpis_from_page","args":{"text": agg},"id":"tc_kpi","type":"tool_call"}])]})
    kpi = _parse(res1["messages"][0].content) or {}
    if not all(x in kpi for x in ["p_e_ratio","p_s_ratio","gross_margin","operating_margin"]):
        res1b = kpi_node.invoke({"messages":[AIMessage(content="", tool_calls=[{"name":"kpi_web_fallback","args":{"ticker_or_query": t or q},"id":"tc_kpi_fb","type":"tool_call"}])]})
        fb = _parse(res1b["messages"][0].content) or {}
        if isinstance(fb, dict): kpi.update(fb)
    # Projection
    chart_node = ToolNode([price_projection_chart])
    res2 = chart_node.invoke({"messages":[AIMessage(content="", tool_calls=[{"name":"price_projection_chart","args":{"ticker": t or q, "kpi": kpi},"id":"tc_proj","type":"tool_call"}])]})
    proj = _parse(res2["messages"][0].content) or {}
    p5 = proj.get("proj_5y"); p10 = proj.get("proj_10y")
    # Sources
    sources_url = _render_sources_json(q, docs)
    html = render_report(q, t, state.get("summary",""), kpi, state.get("checked_claims",[]), sources_url, f"/outputs/{os.path.basename(p5)}" if p5 else None, f"/outputs/{os.path.basename(p10)}" if p10 else None)
    out = os.path.join(OUTPUTS_DIR, f"report_{int(time.time())}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    state["report_html"] = out
    return state
