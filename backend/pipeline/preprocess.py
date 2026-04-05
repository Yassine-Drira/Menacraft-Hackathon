"""
Preprocessing pipeline for VerifyAI.
Handles image loading and video frame extraction.
"""

import io
import tempfile
from typing import List

import cv2
import numpy as np
from PIL import Image

from pipeline.ingest import is_video_file

MAX_VIDEO_FRAMES = 8
TEMP_VIDEO_FILE = tempfile.mktemp(suffix=".mp4")


def image_from_bytes(data: bytes) -> Image.Image:
    """Load image from bytes."""
    return Image.open(io.BytesIO(data)).convert("RGB")


def extract_key_frames(video_bytes: bytes, max_frames: int = MAX_VIDEO_FRAMES) -> List[Image.Image]:
    """
    Extract key frames from video using evenly spaced sampling.
    """
    # Write video to temporary file
    with open(TEMP_VIDEO_FILE, "wb") as f:
        f.write(video_bytes)

    try:
        capture = cv2.VideoCapture(TEMP_VIDEO_FILE)
        if not capture.isOpened():
            raise ValueError("Could not open video file")

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            raise ValueError("Video has no frames")

        # Calculate frame positions (evenly spaced)
        if total_frames <= max_frames:
            positions = list(range(total_frames))
        else:
            step = total_frames / max_frames
            positions = [int(i * step) for i in range(max_frames)]

        frames = []
        for pos in positions:
            capture.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = capture.read()
            if ret:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(rgb_frame))

        capture.release()
        return frames

    finally:
        # Clean up temp file
        try:
            os.unlink(TEMP_VIDEO_FILE)
        except OSError:
            pass


def preprocess_media(media_bytes: bytes, content_type: str) -> List[Image.Image]:
    """
    Preprocess media file into list of PIL Images.
    For images: single image in list
    For videos: list of key frames
    """
    if is_video_file(content_type):
        return extract_key_frames(media_bytes)
    else:
        # Assume image
        return [image_from_bytes(media_bytes)]