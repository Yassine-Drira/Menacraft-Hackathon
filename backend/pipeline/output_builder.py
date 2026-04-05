"""
Output builder for VerifyAI.
Assembles the final bilan JSON response.
"""

import time
from typing import Dict, List, Optional


def build_early_exit_bilan(
    clip_score: float,
    processing_time_ms: int
) -> Dict:
    """Build bilan for early exit case."""
    score = int(clip_score * 100)

    return {
        "score": score,
        "verdict": "MISMATCH",
        "early_exit": True,
        "clip_score": clip_score,
        "flags": ["semantic_mismatch"],
        "blip_description": None,
        "entities": None,
        "explanation": "The image and caption are semantically unrelated (CLIP similarity: {:.2f}). The visual content has no meaningful connection to the claim being made. No further analysis was necessary.".format(clip_score),
        "evidence": None,
        "processing_time_ms": processing_time_ms
    }


def build_full_bilan(
    score: int,
    verdict: str,
    clip_score: float,
    flags: List[str],
    blip_description: str,
    entities: Dict[str, List[str]],
    explanation: str,
    evidence: Optional[List[Dict[str, str]]],
    processing_time_ms: int
) -> Dict:
    """Build bilan for full pipeline case."""
    return {
        "score": score,
        "verdict": verdict,
        "early_exit": False,
        "clip_score": clip_score,
        "flags": flags,
        "blip_description": blip_description,
        "entities": entities,
        "explanation": explanation,
        "evidence": evidence,
        "processing_time_ms": processing_time_ms
    }