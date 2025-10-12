
from app.agents.tools import tools as T

def test_http_fetch_title():
    r = T.http_fetch.invoke({"url":"https://example.com"})
    assert isinstance(r, dict) and "title" in r

def test_kpi_fallback_works_smoke():
    r = T.kpi_web_fallback.invoke({"ticker_or_query":"AAPL"})
    assert isinstance(r, dict)
