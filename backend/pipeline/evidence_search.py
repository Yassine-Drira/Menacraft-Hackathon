"""
Evidence search layer for VerifyAI.
Uses DuckDuckGo to find supporting or contradicting evidence.
"""

import time
from typing import Dict, List, Optional

from duckduckgo_search import DDGS


def search_evidence(caption: str, entities: Dict[str, List[str]], max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for evidence related to the caption claims.
    Returns list of evidence items with title, url, snippet.
    """
    # Build search query from entities
    query_parts = []

    if entities.get("locations"):
        query_parts.extend(entities["locations"])

    if entities.get("events"):
        query_parts.extend(entities["events"])

    # Add current year for recency
    current_year = time.strftime("%Y")
    query_parts.append(current_year)

    if not query_parts:
        # Fallback to caption keywords
        query_parts = caption.split()[:3]

    query = " ".join(query_parts)

    try:
        # Search with DuckDuckGo using DDGS
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))

        evidence = []
        for item in results[:max_results]:
            evidence.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")
            })

        return evidence

    except Exception:
        # Return empty list on any error
        return []


def score_evidence_relevance(evidence: List[Dict[str, str]], entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """Add relevance scores to evidence items."""
    if not evidence:
        return evidence

    # Simple relevance scoring based on entity matches
    for item in evidence:
        relevance_score = 0
        text = (item["title"] + " " + item["snippet"]).lower()

        for location in entities["locations"]:
            if location.lower() in text:
                relevance_score += 1

        for event in entities["events"]:
            if event.lower() in text:
                relevance_score += 1

        item["relevance_score"] = relevance_score

    return evidence


def detect_evidence_contradiction(evidence: List[Dict[str, str]], entities: Dict[str, List[str]]) -> bool:
    """Check if evidence contradicts the caption claims."""
    # Simple heuristic: if we have evidence but low relevance scores
    relevant_count = sum(1 for item in evidence if item.get("relevance_score", 0) > 0)
    return len(evidence) > 0 and relevant_count == 0