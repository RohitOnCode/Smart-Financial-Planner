"""Agent package with shared role definitions.

This module centralizes human-readable descriptions of each agent's role and
specialization so the responsibilities are clear to contributors and the UI or
telemetry layers can surface them if needed.
"""

from typing import Dict, List

AGENT_ROLES: Dict[str, Dict[str, List[str] | str]] = {
    "researcher": {
        "role": "Lead information gatherer",
        "specializations": [
            "Runs targeted web searches to collect up-to-date sources",
            "Fetches and normalizes raw pages for downstream processing",
            "Attaches trace metadata so the research path is auditable",
        ],
    },
    "curator": {
        "role": "Evidence organizer",
        "specializations": [
            "Indexes retrieved documents and selects the most relevant",
            "Generates concise summaries tailored to the user query",
            "Prepares cleaned excerpts for fact-checking and reporting",
        ],
    },
    "fact_checker": {
        "role": "Quality and accuracy gate",
        "specializations": [
            "Extracts claims from the curated summary",
            "Cross-verifies claims against retrieved evidence with overlap rules",
            "Flags unverifiable statements for transparency",
        ],
    },
    "writer": {
        "role": "Report assembler",
        "specializations": [
            "Aggregates KPIs and projections for the requested ticker or topic",
            "Builds the final HTML report with links back to sources",
            "Persists artifacts (sources JSON, projection charts) for the UI",
        ],
    },
}


def get_agent_roles() -> Dict[str, Dict[str, List[str] | str]]:
    """Return a copy of the agent role map for safe external use."""

    return AGENT_ROLES.copy()
