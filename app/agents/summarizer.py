
import os
from typing import List, Dict, Any
from app.agents.base import get_llm
from app.config import BASE_DIR

def _load_prompt(name: str, **kwargs) -> str:
    path = os.path.join(os.path.dirname(BASE_DIR), "prompts", name)
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    return txt.format(**kwargs)

def summarize_docs(docs: List[Dict[str, Any]], query: str) -> str:
    excerpts = []
    for d in docs[:8]:
        excerpts.append(f"TITLE: {d.get('title','')[:80]}\nURL: {d.get('url','')}\nTEXT: {d.get('text','')[:1500]}")
    prompt = _load_prompt("summarize.txt", query=query, excerpts="\n".join(excerpts))
    try:
        llm = get_llm(temperature=0.2)
        r = llm.invoke(prompt)
        out = (r.content if hasattr(r,'content') else str(r)).strip()
        if out: return out
    except Exception: pass
    bullets = []
    for d in docs[:5]:
        title = d.get("title","")[:120]; url = d.get("url",""); snip = (d.get("text","") or "")[:280].replace("\n"," ")
        bullets.append(f"- {title} — {snip} [{url}]")
    return "Key points from retrieved sources (heuristic summary):\n" + "\n".join(bullets)
