
from typing import List, Dict, Any, Optional, TypedDict

class ResearchState(TypedDict, total=False):
    query: str
    ticker: Optional[str]
    web_results: List[Dict[str, Any]]
    docs: List[Dict[str, Any]]
    summary: str
    claims: List[str]
    checked_claims: List[Dict[str, Any]]
    report_html: Optional[str]
    trace: List[Dict[str, Any]]
