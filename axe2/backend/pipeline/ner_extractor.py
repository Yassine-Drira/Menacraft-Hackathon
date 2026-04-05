"""
Named Entity Recognition extractor for VerifyAI.
Uses spaCy to extract entities from captions.
"""

import spacy
from typing import Dict, List

# Temporal keywords that indicate unverifiable time claims
TEMPORAL_KEYWORDS = [
    "today", "tonight", "now", "this morning", "this evening",
    "yesterday", "current", "breaking", "just now", "this week",
    "this month", "right now", "happening now", "live", "currently",
    "at this moment"
]

# Event type keywords for mismatch detection
EVENT_KEYWORDS = {
    "protest": ["protest", "demonstration", "riot", "march", "strike"],
    "flood": ["flood", "inundation", "water damage", "deluge"],
    "celebration": ["celebration", "festival", "party", "parade"],
    "accident": ["accident", "crash", "collision", "wreck"],
    "fire": ["fire", "blaze", "smoke", "inferno"],
}


def load_spacy_model() -> spacy.Language:
    """Load spaCy model with fallback."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # Try to download if not available
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
        return spacy.load("en_core_web_sm")


# Global spaCy model
_nlp = None

def get_nlp() -> spacy.Language:
    """Get cached spaCy model."""
    global _nlp
    if _nlp is None:
        _nlp = load_spacy_model()
    return _nlp


def extract_entities(caption: str) -> Dict[str, List[str]]:
    """Extract named entities from caption."""
    nlp = get_nlp()
    doc = nlp(caption)

    entities = {
        "locations": [],
        "dates": [],
        "events": [],
        "persons": [],
        "temporal_flags": []
    }

    # Extract entities
    for ent in doc.ents:
        if ent.label_ in {"GPE", "LOC"}:
            entities["locations"].append(ent.text)
        elif ent.label_ == "DATE":
            entities["dates"].append(ent.text)
        elif ent.label_ == "EVENT":
            entities["events"].append(ent.text)
        elif ent.label_ == "PERSON":
            entities["persons"].append(ent.text)

    # Check for temporal keywords
    caption_lower = caption.lower()
    for keyword in TEMPORAL_KEYWORDS:
        if keyword in caption_lower:
            entities["temporal_flags"].append(keyword)

    # Remove duplicates
    for key in entities:
        entities[key] = list(dict.fromkeys(entities[key]))

    return entities


def detect_event_type(caption: str) -> str:
    """Detect event type from caption keywords."""
    caption_lower = caption.lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(keyword in caption_lower for keyword in keywords):
            return event_type
    return ""