"""
CLIP early exit gate for VerifyAI.
Computes semantic similarity between image and caption.
"""

from typing import List
import numpy as np
import torch
from PIL import Image

from models.loader import get_clip

CLIP_THRESHOLD = 0.25


def clip_similarity(image: Image.Image, caption: str) -> float:
    """Compute CLIP similarity between image and caption."""
    clip_model, clip_processor = get_clip()

    inputs = clip_processor(
        text=caption,
        images=image,
        return_tensors="pt",
        padding=True
    )
    

    with torch.no_grad():
        outputs = clip_model(**inputs)

    # Compute cosine similarity
    image_emb = outputs.image_embeds
    text_emb = outputs.text_embeds

    # Normalize embeddings
    image_emb = image_emb / image_emb.norm(p=2, dim=-1, keepdim=True)
    text_emb = text_emb / text_emb.norm(p=2, dim=-1, keepdim=True)

    similarity = (image_emb @ text_emb.T).squeeze().item()
    return float(np.clip(similarity, -1.0, 1.0))


def get_best_clip_score(frames: List[Image.Image], caption: str) -> float:
    """Get best CLIP score across multiple frames."""
    if not frames:
        return 0.0

    scores = [clip_similarity(frame, caption) for frame in frames]
    return max(scores)


def should_early_exit(clip_score: float) -> bool:
    """Check if CLIP score indicates early exit."""
    return clip_score < CLIP_THRESHOLD


def get_verdict_from_clip_score(clip_score: float) -> str:
    """Get verdict based on CLIP score."""
    if clip_score < CLIP_THRESHOLD:
        return "MISMATCH"
    elif clip_score < 0.28:
        return "SUSPICIOUS"
    else:
        return "LIKELY_MATCH"