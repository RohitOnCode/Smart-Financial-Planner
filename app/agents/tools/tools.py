
import os, re, json, time, ast
import requests
import numpy as np
import pandas as pd
import yfinance as yf
import seaborn as sns
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.config import OUTPUTS_DIR
from app.agents.base import get_llm

# ------------- helpers -------------
def _parse_tool_content(content):
    if isinstance(content, (list, dict)):
        return content
    if content is None:
        return None
    s = str(content)
    try:
        return json.loads(s)
    except Exception:
        try:
            return ast.literal_eval(s)
        except Exception:
            return s

def _extract_title(html: str) -> str:
    try:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I|re.S)
        if m: return re.sub(r"\s+", " ", m.group(1)).strip()
    except Exception:
        pass
    return ""

# ------------- web search -------------
try:
    from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
    _ddg = DuckDuckGoSearchRun()
except Exception:
    _ddg = None
try:
    from ddgs import DDGS
except Exception:
    DDGS = None

@tool
def web_search(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Search the web (DuckDuckGo). Returns list of {title, snippet, link}."""
    out: List[Dict[str, Any]] = []
    def norm(r):
        return {
            "title": r.get("title") or r.get("t") or "",
            "snippet": r.get("snippet") or r.get("body") or r.get("abstract") or "",
            "link": r.get("link") or r.get("href") or r.get("url") or "",
        }
    if _ddg:
        try:
            r = _ddg.invoke({"query": query})
            if isinstance(r, list):
                out.extend([norm(x) for x in r])
            elif isinstance(r, dict):
                out.append(norm(r))
        except Exception as e:
            out.append({"title":"ddg_error","snippet":str(e),"link":""})
    if DDGS and len([x for x in out if x.get("link")]) < 3:
        try:
            with DDGS() as dd:
                for hit in dd.text(query, safesearch="off", max_results=max_results*2):
                    out.append(norm(hit))
        except Exception as e:
            out.append({"title":"ddgs_error","snippet":str(e),"link":""})
    # dedupe
    seen=set(); final=[]
    for x in out:
        key=x.get("link") or x.get("title")
        if key and key not in seen:
            seen.add(key); final.append(x)
    return final[:max_results]

@tool
def http_fetch(url: str, timeout: int = 15) -> Dict[str, Any]:
    """HTTP GET a URL and return {url,status,title,text[:60k]}"""
    if not url:
        return {"url":"", "status":0, "title":"", "text":""}
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        html = r.text[:60000]
        return {"url": url, "status": r.status_code, "title": _extract_title(html), "text": html}
    except Exception as e:
        return {"url": url, "status": 0, "error": str(e), "title": "", "text": ""}

# ------------- KPIs -------------
KPI_PATTERNS = {
    "p_e_ratio": [
        r"P\/E\s*(?:ratio|)\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)",
        r"\bPE\s*ratio\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)",
    ],
    "p_s_ratio": [
        r"P\/S\s*(?:ratio|)\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)",
        r"price\s*to\s*sales\s*(?:ratio|)\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)",
    ],
    "gross_margin": [
        r"gross\s*margin(?:\s*%|\s*percentage|)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
    ],
    "operating_margin": [
        r"operating\s*margin(?:\s*%|\s*percentage|)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
    ],
}

def _extract_first(text: str, patterns: List[str]):
    t = text.lower()
    for pat in patterns:
        m = re.search(pat, t, re.I)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
    return None

@tool
def extract_kpis_from_page(text: str) -> Dict[str, Any]:
    """Extract KPI values (PE, PS, gross margin, operating margin) from raw HTML/text."""
    found: Dict[str, Any] = {}
    for k, patterns in KPI_PATTERNS.items():
        val = _extract_first(text, patterns)
        if val is None: 
            continue
        if k in ("gross_margin","operating_margin"):
            val = val / 100.0
        found[k] = val
    return found

def _kpi_from_yfinance(ticker: str) -> Dict[str, Any]:
    out = {}
    try:
        tk = yf.Ticker(ticker)
        info = getattr(tk, "info", {}) or {}
        price = None
        try:
            hist = tk.history(period="5d", interval="1d", auto_adjust=True)
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        except Exception:
            pass

        pe = info.get("trailingPE") or None
        eps = info.get("trailingEps") or None
        if not pe and price and eps and eps != 0:
            pe = price / eps
        if pe: out["p_e_ratio"] = float(pe)

        ps = info.get("priceToSalesTrailing12Months") or None
        if ps: out["p_s_ratio"] = float(ps)

        # Margins from financials if possible
        try:
            fin = tk.financials  # annual
            if fin is not None and not fin.empty:
                latest_col = fin.columns[0]
                def getv(row):
                    try:
                        return float(fin.loc[row, latest_col])
                    except Exception:
                        return None
                rev = getv("Total Revenue")
                gp = getv("Gross Profit")
                op = getv("Operating Income")
                if rev and gp is not None:
                    out["gross_margin"] = float(gp) / float(rev)
                if rev and op is not None:
                    out["operating_margin"] = float(op) / float(rev)
        except Exception:
            pass
    except Exception:
        pass
    return out

@tool
def kpi_web_fallback(ticker_or_query: str) -> Dict[str, Any]:
    """Search the web for KPI values; if still missing, compute via yfinance."""
    results = {}
    queries = [
        f"{ticker_or_query} P/E ratio", f"{ticker_or_query} price to sales ratio",
        f"{ticker_or_query} gross margin percentage", f"{ticker_or_query} operating margin percentage",
        f"{ticker_or_query} KPIs financial ratios"
    ]
    hits_all = []
    for q in queries:
        hits = web_search.invoke({"query": q, "max_results": 6}) or []
        hits_all.extend(hits)
    for h in hits_all:
        url = h.get("link") or h.get("url") or ""
        page = http_fetch.invoke({"url": url}) if url else {"text": h.get("snippet",""), "title": ""}
        text = page.get("text","") or h.get("snippet","")
        if not text:
            continue
        k = extract_kpis_from_page.invoke({"text": text}) or {}
        for kk, vv in k.items():
            if vv is not None and kk not in results:
                results[kk] = vv
        if all(x in results for x in ["p_e_ratio","p_s_ratio","gross_margin","operating_margin"]):
            break
    # yfinance fallback
    yk = _kpi_from_yfinance(ticker_or_query)
    for kk, vv in yk.items():
        results.setdefault(kk, vv)
    return results

# ------------- Embeddings / FAISS with metadata -------------
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

_INDEX_REG: Dict[str, Any] = {}

@tool
def build_index(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build an embedding index from a list of docs (expects each to have 'text', 'url', 'title').
    Returns {"ok": True, "key": key, "size": N}.
    """
    if not docs:
        return {"ok": False, "msg": "no docs"}
    emb = OpenAIEmbeddings()
    lang_docs = []
    for d in docs:
        txt = (d.get("text") or "")[:3000]
        if not txt.strip():
            continue
        lang_docs.append(Document(page_content=txt, metadata={
            "url": d.get("url",""), "title": d.get("title","")
        }))
    if not lang_docs:
        return {"ok": False, "msg": "no valid text"}
    store = FAISS.from_documents(lang_docs, emb)
    key = f"idx_{int(time.time()*1000)}"
    _INDEX_REG[key] = store
    return {"ok": True, "key": key, "size": len(lang_docs)}

@tool
def search_index(key: str, query: str, k: int = 6) -> List[Dict[str, Any]]:
    """Search an existing embedding index by key. Returns list with text + metadata (url/title)."""
    store = _INDEX_REG.get(key)
    if not store:
        return []
    docs = store.similarity_search(query, k=k)
    return [{"text": d.page_content, "metadata": d.metadata} for d in docs]

# ------------- Claims tools -------------
@tool
def extract_claims_tool(summary: str, topic: str, n: int = 6) -> List[str]:
    """LLM-based claim extractor. Returns a list of claims (strings)."""
    from app.config import BASE_DIR
    path = os.path.join(os.path.dirname(BASE_DIR), "prompts", "extract_claims.txt")
    with open(path, "r", encoding="utf-8") as f:
        tmpl = f.read()
    prompt = tmpl.format(summary=summary, topic=topic, n=n)
    try:
        llm=get_llm(temperature=0.0)
        r=llm.invoke(prompt); txt=r.content if hasattr(r,'content') else str(r)
        lines=[l.strip(" -•") for l in txt.splitlines() if l.strip()]
        return lines[:n]
    except Exception:
        return []

@tool
def verify_claims_tool(claims: List[str], sources: List[Dict[str, Any]], min_overlap: int = 1) -> List[Dict[str, Any]]:
    """Heuristic verifier by token overlap against source texts. Returns list of {claim, verdict, evidence_url}."""
    import re
    out=[]
    for c in claims:
        toks=[t for t in re.findall(r"[A-Za-z0-9\-]+", c.lower()) if len(t)>3]
        verdict=False; url=None; overlap_max=0
        for s in sources:
            text=(s.get('text','') or '').lower()
            overlap=sum(1 for t in toks if t in text)
            if overlap>overlap_max:
                overlap_max=overlap; url=s.get('url') or (s.get('metadata') or {}).get('url')
            if overlap>=min_overlap:
                verdict=True
        out.append({"claim":c,"verdict":verdict,"evidence_url":url,"note":f"overlap={overlap_max}"})
    return out

# ------------- Price projection -------------
def _get_current_price(ticker: str) -> Optional[float]:
    try:
        hist = yf.Ticker(ticker).history(period='5d', interval='1d', auto_adjust=True)
        if hist is None or hist.empty: return None
        return float(hist['Close'].iloc[-1])
    except Exception:
        return None

def _estimate_growth(kpi: Dict[str, Any], momentum: Optional[float]=None, cagr: Optional[float]=None):
    base = 0.08
    gm = kpi.get("gross_margin"); om = kpi.get("operating_margin"); pe = kpi.get("p_e_ratio")
    adj = 0.0
    if gm: adj += min(max((gm-0.35)*0.5, -0.05), 0.10)
    if om: adj += min(max((om-0.15)*0.7, -0.05), 0.12)
    if pe and pe>0:
        if pe<20: adj += 0.02
        elif pe>50: adj -= 0.03
    if cagr is not None: adj += np.clip(cagr*0.5, -0.05, 0.10)
    if momentum is not None: adj += np.clip(momentum*0.3, -0.05, 0.06)
    return max(base + adj, 0.01)

@tool
def price_projection_chart(ticker: str, kpi: Dict[str, Any], momentum_3m: Optional[float]=None, cagr_3y: Optional[float]=None) -> Dict[str, Any]:
    """Create 5-year and 10-year price projection charts using a heuristic growth model. Returns image paths."""
    p0 = _get_current_price(ticker) or 100.0
    g = _estimate_growth(kpi, momentum_3m, cagr_3y)
    years_5 = np.arange(0, 5.01, 0.25)
    years_10 = np.arange(0, 10.01, 0.25)
    proj5 = p0 * (1+g) ** years_5
    proj10 = p0 * (1+g) ** years_10
    sns.set()
    import matplotlib.pyplot as plt
    fig = plt.figure()
    plt.plot(years_5, proj5)
    plt.xlabel("Years"); plt.ylabel("Projected Price"); plt.title(f"{ticker} — 5Y Projection (g~{g*100:.1f}%)")
    plt.tight_layout()
    p5_path = os.path.join(OUTPUTS_DIR, f"{ticker}_proj_5y_{int(time.time())}.png")
    plt.savefig(p5_path, dpi=160); plt.close(fig)
    fig = plt.figure()
    plt.plot(years_10, proj10)
    plt.xlabel("Years"); plt.ylabel("Projected Price"); plt.title(f"{ticker} — 10Y Projection (g~{g*100:.1f}%)")
    plt.tight_layout()
    p10_path = os.path.join(OUTPUTS_DIR, f"{ticker}_proj_10y_{int(time.time())}.png")
    plt.savefig(p10_path, dpi=160); plt.close(fig)
    return {"g": g, "p0": p0, "proj_5y": p5_path, "proj_10y": p10_path}
