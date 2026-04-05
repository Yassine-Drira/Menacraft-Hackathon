"""
VerifyAI FastAPI backend.
Main application with multimodal verification pipeline.
"""

import logging
import time
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.loader import load_all_models
from pipeline.ingest import validate_file, validate_caption, is_video_file
from pipeline.preprocess import preprocess_media
from pipeline.clip_gate import get_best_clip_score, should_early_exit
from pipeline.blip_captioner import generate_caption
from pipeline.ner_extractor import extract_entities
from pipeline.comparator import compare_consistency
from pipeline.evidence_search import search_evidence, score_evidence_relevance
from pipeline.output_builder import build_early_exit_bilan, build_full_bilan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="VerifyAI",
    description="Multimodal context verification system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load all models at startup."""
    logger.info("Starting VerifyAI backend...")
    load_all_models()
    logger.info("All models loaded successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "VerifyAI backend is running",
        "models_loaded": True
    }


@app.post("/verify")
async def verify(
    media: UploadFile = File(...),
    caption: str = Form(...),
    search_enabled: bool = Form(False)
):
    """
    Main verification endpoint.
    Accepts media file + caption and returns consistency analysis.
    """
    start_time = time.time()

    try:
        # Validate inputs
        validate_file(media)
        validate_caption(caption)

        # Read file content
        content = await media.read()

        # Preprocess media
        frames = preprocess_media(content, media.content_type)

        if not frames:
            raise HTTPException(status_code=400, detail="Could not process media file")

        # CLIP early exit gate
        clip_score = get_best_clip_score(frames, caption)

        if should_early_exit(clip_score):
            processing_time = int((time.time() - start_time) * 1000)
            return JSONResponse(content=build_early_exit_bilan(clip_score, processing_time))

        # Full pipeline - find best frame for BLIP
        best_frame = frames[0]  # Could be improved to use frame with highest CLIP score

        # Generate BLIP caption
        blip_description = generate_caption(best_frame)

        # Extract entities from caption
        entities = extract_entities(caption)

        # Compare consistency
        comparison = compare_consistency(clip_score, blip_description, entities)

        # Optional evidence search
        evidence = None
        if search_enabled:
            evidence = search_evidence(caption, entities)
            evidence = score_evidence_relevance(evidence, entities)

        # Build final response
        processing_time = int((time.time() - start_time) * 1000)
        bilan = build_full_bilan(
            score=comparison["score"],
            verdict=comparison["verdict"],
            clip_score=clip_score,
            flags=comparison["flags"],
            blip_description=blip_description,
            entities=entities,
            explanation=comparison["explanation"],
            evidence=evidence,
            processing_time_ms=processing_time
        )

        return JSONResponse(content=bilan)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal processing error: {str(e)}")