"""
CLIP early exit gate for VerifyAI.
Computes semantic similarity between image and caption.
"""

from typing import List, Tuple
import numpy as np
import torch
from PIL import Image

from models.loader import get_clip

# ── Thresholds operate on NORMALIZED scores (0.0–1.0) ──────────────
# clip-vit-base-patch32 raw cosine scores cluster in 0.05–0.38
# After normalization: 0.15 raw → ~0.27 norm, 0.28 raw → ~0.70 norm
CLIP_EARLY_EXIT_THRESHOLD = 0.25   # normalized — below this → instant MISMATCH
CLIP_SUSPICIOUS_THRESHOLD = 0.45   # normalized — below this → SUSPICIOUS

# Empirical bounds for clip-vit-base-patch32 on natural images
# Raw scores outside this range are extremely rare
_RAW_MIN = 0.05
_RAW_MAX = 0.38


def _normalize(raw: float) -> float:
    """
    Rescale raw CLIP cosine similarity into a 0.0–1.0 range.

    Why: clip-vit-base-patch32 raw cosine scores are naturally compressed.
    Even a perfectly matched image+caption pair rarely exceeds 0.35.
    Raw scores are meaningless to humans — normalized scores are not.

    Examples with these bounds:
        raw 0.05 → 0.00  (completely unrelated)
        raw 0.15 → 0.30  (weakly related)
        raw 0.22 → 0.52  (moderately related)
        raw 0.28 → 0.70  (well matched)
        raw 0.35 → 0.91  (strongly matched)
        raw 0.38 → 1.00  (ceiling)
    """
    return float(np.clip((raw - _RAW_MIN) / (_RAW_MAX - _RAW_MIN), 0.0, 1.0))


def clip_similarity(image: Image.Image, caption: str) -> dict:
    """
    Compute CLIP similarity between image and caption.

    Returns a dict with:
        raw        — original cosine similarity (keep for debugging)
        normalized — rescaled 0.0–1.0 (use for thresholds)
        display    — integer 0–100 (use for UI / output bilan)
    """
    clip_model, clip_processor = get_clip()

    inputs = clip_processor(
        text=[caption],
        images=image,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=77       # CLIP hard token limit
    )

    # Move inputs to same device as model
    device = next(clip_model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = clip_model(**inputs)

    image_emb = outputs.image_embeds
    text_emb  = outputs.text_embeds

    image_emb = image_emb / image_emb.norm(p=2, dim=-1, keepdim=True)
    text_emb  = text_emb  / text_emb.norm(p=2, dim=-1, keepdim=True)

    raw        = float(np.clip((image_emb @ text_emb.T).squeeze().item(), -1.0, 1.0))
    normalized = _normalize(raw)

    return {
        "raw":        round(raw, 4),
        "normalized": round(normalized, 4),
        "display":    int(round(normalized * 100))
    }


def get_best_clip_score(frames: List[Image.Image], caption: str) -> Tuple[dict, int]:
    """
    Get best CLIP score across multiple frames (video / reels).

    Strategy: take the frame with the highest raw score.
    One strongly matching frame is enough to justify deep analysis.

    Returns (best_score_dict, best_frame_index).
    """
    if not frames:
        return {"raw": 0.0, "normalized": 0.0, "display": 0}, -1

    scores   = [clip_similarity(frame, caption) for frame in frames]
    best_idx = int(np.argmax([s["raw"] for s in scores]))

    return scores[best_idx], best_idx


def should_early_exit(clip_score: dict) -> bool:
    """Trigger early exit if normalized score is below threshold."""
    return clip_score["normalized"] < CLIP_EARLY_EXIT_THRESHOLD


def get_verdict_from_clip_score(clip_score: dict) -> str:
    """Get verdict band from normalized score."""
    n = clip_score["normalized"]
    if n < CLIP_EARLY_EXIT_THRESHOLD:
        return "MISMATCH"
    elif n < CLIP_SUSPICIOUS_THRESHOLD:
        return "SUSPICIOUS"
    else:
        return "LIKELY_MATCH"