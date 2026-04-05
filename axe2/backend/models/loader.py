"""
Model loader for VerifyAI backend.
Loads and caches all AI models at startup.
"""

import logging
from typing import Optional, Tuple

from transformers import CLIPModel, CLIPProcessor, BlipProcessor, BlipForConditionalGeneration

logger = logging.getLogger(__name__)

# Global model cache
clip_model: Optional[CLIPModel] = None
clip_processor: Optional[CLIPProcessor] = None
blip_model: Optional[BlipForConditionalGeneration] = None
blip_processor: Optional[BlipProcessor] = None


def load_clip() -> Tuple[CLIPModel, CLIPProcessor]:
    """Load CLIP model and processor."""
    global clip_model, clip_processor
    if clip_model is None or clip_processor is None:
        logger.info("Loading CLIP model...")
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        logger.info("CLIP model loaded successfully")
    return clip_model, clip_processor


def load_blip() -> Tuple[BlipForConditionalGeneration, BlipProcessor]:
    """Load BLIP model and processor."""
    global blip_model, blip_processor
    if blip_model is None or blip_processor is None:
        logger.info("Loading BLIP model...")
        blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        logger.info("BLIP model loaded successfully")
    return blip_model, blip_processor


def load_all_models() -> None:
    """Load all models at startup."""
    logger.info("Loading all AI models...")
    load_clip()
    load_blip()
    logger.info("All models loaded successfully")


def get_clip() -> Tuple[CLIPModel, CLIPProcessor]:
    """Get cached CLIP model and processor."""
    if clip_model is None or clip_processor is None:
        return load_clip()
    return clip_model, clip_processor


def get_blip() -> Tuple[BlipForConditionalGeneration, BlipProcessor]:
    """Get cached BLIP model and processor."""
    if blip_model is None or blip_processor is None:
        return load_blip()
    return blip_model, blip_processor