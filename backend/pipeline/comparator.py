"""
Consistency comparator for VerifyAI.
Cross-references all signals to detect inconsistencies and calculate scores.
"""

from typing import Dict, List

import numpy as np

from .ner_extractor import detect_event_type


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def detect_location_mismatch(entities: Dict[str, List[str]], blip_description: str) -> bool:
    """Check if caption claims locations not present in BLIP description."""
    if not entities["locations"]:
        return False

    blip_lower = normalize_text(blip_description)
    return not any(
        normalize_text(loc) in blip_lower
        for loc in entities["locations"]
    )


def detect_temporal_claim(entities: Dict[str, List[str]]) -> bool:
    """Check if caption makes temporal claims."""
    return len(entities["temporal_flags"]) > 0


def detect_event_mismatch(entities: Dict[str, List[str]], blip_description: str) -> bool:
    """Check if caption event type contradicts BLIP description."""
    caption_event = detect_event_type(" ".join(entities["events"]))
    if not caption_event:
        return False

    blip_lower = normalize_text(blip_description)
    return caption_event not in blip_lower


def detect_overclaiming(entities: Dict[str, List[str]]) -> bool:
    """Check if caption makes multiple specific unverifiable claims."""
    specific_claims = (
        len(entities["locations"]) +
        len(entities["dates"]) +
        len(entities["persons"])
    )
    return specific_claims >= 3


def calculate_score(
    clip_score: float,
    flags: List[str],
    entities: Dict[str, List[str]]
) -> int:
    """Calculate final consistency score."""
    # Base score from CLIP (0-100)
    base_score = int(np.clip(clip_score * 100, 0, 100))

    # Apply penalties
    penalties = {
        "location_mismatch": 25,
        "temporal_claim_unverifiable": 15,
        "event_type_mismatch": 30,
        "overclaiming_specificity": 10,
        "evidence_contradicts_claim": 15
    }

    total_penalty = sum(penalties.get(flag, 0) for flag in flags)

    return max(0, base_score - total_penalty)


def get_verdict(score: int) -> str:
    """Get verdict from score."""
    if score >= 70:
        return "CONSISTENT"
    elif score >= 35:
        return "SUSPICIOUS"
    else:
        return "MISMATCH"


def generate_explanation(
    clip_score: float,
    blip_description: str,
    entities: Dict[str, List[str]],
    flags: List[str],
    verdict: str
) -> str:
    """Generate human-readable explanation."""
    explanations = []

    if "location_mismatch" in flags and entities["locations"]:
        locations = ", ".join(entities["locations"])
        explanations.append(
            f"The caption claims a location in {locations}, but the image description does not include those location cues."
        )

    if "temporal_claim_unverifiable" in flags:
        explanations.append(
            "The caption uses a specific time claim that cannot be verified visually from the media."
        )

    if "event_type_mismatch" in flags:
        caption_event = detect_event_type(" ".join(entities["events"]))
        explanations.append(
            f"The caption suggests an event like {caption_event}, but the image appears to describe a different scene."
        )

    if "overclaiming_specificity" in flags:
        explanations.append(
            "The caption makes multiple specific claims that are not supported by the visual content."
        )

    if not explanations:
        if verdict == "CONSISTENT":
            explanations.append(
                "The caption and visual content are generally consistent based on model analysis."
            )
        else:
            explanations.append(
                "While there are no specific inconsistencies detected, the semantic alignment between caption and image is weak."
            )

    return " ".join(explanations)


def compare_consistency(
    clip_score: float,
    blip_description: str,
    entities: Dict[str, List[str]]
) -> Dict:
    """Main consistency comparison function."""
    flags = []

    # Detect inconsistencies
    if detect_location_mismatch(entities, blip_description):
        flags.append("location_mismatch")

    if detect_temporal_claim(entities):
        flags.append("temporal_claim_unverifiable")

    if detect_event_mismatch(entities, blip_description):
        flags.append("event_type_mismatch")

    if detect_overclaiming(entities):
        flags.append("overclaiming_specificity")

    # Calculate score and verdict
    score = calculate_score(clip_score, flags, entities)
    verdict = get_verdict(score)

    # Generate explanation
    explanation = generate_explanation(clip_score, blip_description, entities, flags, verdict)

    return {
        "score": score,
        "verdict": verdict,
        "flags": flags,
        "explanation": explanation
    }