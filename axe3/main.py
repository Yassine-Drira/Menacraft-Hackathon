import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models import SourceRequest, SourceResponse
from scorer import compute, quick_compute

_COMPUTE_POOL = ThreadPoolExecutor(max_workers=8)
_DEEP_ANALYSIS_TIMEOUT_SECONDS = 12

app = FastAPI(title="ClipTrust - Source Credibility Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze/source", response_model=SourceResponse)
def analyze_source(req: SourceRequest):
    if not req.url or len(req.url.strip()) < 2:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        account_payload = req.account.model_dump() if req.account else None
        future = _COMPUTE_POOL.submit(
            compute,
            req.url,
            handle=req.handle,
            account=account_payload,
            texts=req.texts,
        )
        try:
            return future.result(timeout=_DEEP_ANALYSIS_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            fallback = quick_compute(req.url)
            fallback_flags = fallback.get("flags", [])
            fallback_flags.append(
                f"Deep analysis timed out after {_DEEP_ANALYSIS_TIMEOUT_SECONDS}s; returned fast fallback"
            )
            fallback["flags"] = fallback_flags
            return fallback
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
def health():
    return {"status": "ok", "axis": "source"}


@app.get("/")
def app_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "index.html")
    return FileResponse(ui_path)
