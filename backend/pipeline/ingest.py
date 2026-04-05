"""
Input ingestion and validation for VerifyAI.
"""

import os
from typing import Tuple

from fastapi import HTTPException, UploadFile

# Supported file types
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_VIDEO_TYPES = {"video/mp4", "video/quicktime"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    if not file.content_type:
        raise HTTPException(status_code=400, detail="File content type not provided")

    if file.content_type not in SUPPORTED_IMAGE_TYPES | SUPPORTED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Supported: {', '.join(SUPPORTED_IMAGE_TYPES | SUPPORTED_VIDEO_TYPES)}"
        )

    # Check file size by seeking to end
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / (1024*1024):.1f}MB. Maximum: {MAX_FILE_SIZE / (1024*1024)}MB"
        )


def validate_caption(caption: str) -> None:
    """Validate caption input."""
    if not caption or not caption.strip():
        raise HTTPException(status_code=400, detail="Caption cannot be empty")

    if len(caption) > 2000:
        raise HTTPException(status_code=400, detail="Caption too long. Maximum 2000 characters")


def is_video_file(content_type: str) -> bool:
    """Check if file is a video."""
    return content_type in SUPPORTED_VIDEO_TYPES


def is_image_file(content_type: str) -> bool:
    """Check if file is an image."""
    return content_type in SUPPORTED_IMAGE_TYPES