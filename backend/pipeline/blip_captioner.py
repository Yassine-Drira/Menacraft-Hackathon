"""
BLIP image captioner for VerifyAI.
Generates natural language descriptions of images.
"""

import logging

from PIL import Image

from models.loader import get_blip

LOGGER = logging.getLogger(__name__)


def generate_caption(image: Image.Image) -> str:
    """Generate caption for image using BLIP."""
    blip_model, blip_processor = get_blip()

    inputs = blip_processor(image, return_tensors="pt")

    # Generate caption
    output = blip_model.generate(**inputs, max_new_tokens=50)
    LOGGER.debug(f"BLIP raw output: {output}")
    caption = blip_processor.decode(output[0], skip_special_tokens=True)
    return caption.strip()