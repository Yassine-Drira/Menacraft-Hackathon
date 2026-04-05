"""
Deepfake Detector – FastAPI Backend
Matches the ThumbnailGridDetector architecture from deepfake-hackathon.ipynb
"""

import io
import os
import tempfile
import traceback
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from torchvision import transforms

# ── Model must match the notebook's architecture exactly ─────────────────────
try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False


class ThumbnailGridDetector(nn.Module):
    """
    Replicates the notebook model.
    N consecutive frames are tiled into a 2-D grid; a single 2-D CNN
    then classifies the whole clip as REAL (0) or FAKE (1).
    """

    def __init__(
        self,
        backbone: str = "efficientnet_b0",
        grid_n: int = 4,           # total frames per clip
        frame_size: int = 112,     # each frame resized to frame_size × frame_size
        num_classes: int = 1,
    ):
        super().__init__()
        self.grid_n = grid_n
        self.frame_size = frame_size
        self.grid_cols = int(grid_n ** 0.5)  # e.g. 2 for grid_n=4
        self.grid_rows = (grid_n + self.grid_cols - 1) // self.grid_cols

        if TIMM_AVAILABLE:
            self.backbone = timm.create_model(
                backbone, pretrained=False, num_classes=num_classes
            )
        else:
            # Fallback: tiny CNN so the server at least starts
            self.backbone = _FallbackCNN(num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


class _FallbackCNN(nn.Module):
    def __init__(self, num_classes: int = 1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.fc = nn.Linear(32, num_classes)

    def forward(self, x):
        return self.fc(self.net(x).flatten(1))


# ── App & Config ──────────────────────────────────────────────────────────────
app = FastAPI(title="Deepfake Detector API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.environ.get("MODEL_PATH", "detector.pth")

# Grid / preprocessing params – must match what the notebook used at training
GRID_N = 4
FRAME_SIZE = 112
GRID_COLS = int(GRID_N ** 0.5)
GRID_ROWS = (GRID_N + GRID_COLS - 1) // GRID_COLS
GRID_H = GRID_ROWS * FRAME_SIZE   # 224
GRID_W = GRID_COLS * FRAME_SIZE   # 224

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

preprocess = transforms.Compose([
    transforms.Resize((GRID_H, GRID_W)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

# ── Model Loading ─────────────────────────────────────────────────────────────
model: ThumbnailGridDetector | None = None


def load_model():
    global model
    m = ThumbnailGridDetector(grid_n=GRID_N, frame_size=FRAME_SIZE).to(DEVICE)
    p = Path(MODEL_PATH)
    if p.exists():
        state = torch.load(p, map_location=DEVICE)
        # Accept plain state-dict or wrapped {"model_state_dict": ...}
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        m.load_state_dict(state, strict=False)
        print(f"✅  Model loaded from {p}")
    else:
        print(f"⚠️  {p} not found – running with random weights (inference will be meaningless)")
    m.eval()
    model = m


@app.on_event("startup")
async def startup_event():
    load_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_frames(video_path: str, n: int = GRID_N) -> list[np.ndarray]:
    """Extract `n` evenly-spaced frames from a video file."""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total < 1:
        raise ValueError("Could not read frames from video.")
    indices = np.linspace(0, max(total - 1, 0), n, dtype=int)
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if ret:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            # Duplicate last valid frame if read fails
            frames.append(frames[-1] if frames else np.zeros((FRAME_SIZE, FRAME_SIZE, 3), np.uint8))
    cap.release()
    # Pad if needed
    while len(frames) < n:
        frames.append(frames[-1])
    return frames[:n]


def build_thumbnail_grid(frames: list[np.ndarray]) -> Image.Image:
    """Tile frames into a GRID_ROWS × GRID_COLS mosaic."""
    resized = [
        cv2.resize(f, (FRAME_SIZE, FRAME_SIZE)) for f in frames
    ]
    rows = []
    for r in range(GRID_ROWS):
        row_frames = resized[r * GRID_COLS: (r + 1) * GRID_COLS]
        # Pad row if short
        while len(row_frames) < GRID_COLS:
            row_frames.append(np.zeros((FRAME_SIZE, FRAME_SIZE, 3), np.uint8))
        rows.append(np.concatenate(row_frames, axis=1))
    grid = np.concatenate(rows, axis=0)
    return Image.fromarray(grid.astype(np.uint8))


def run_inference(pil_image: Image.Image) -> dict:
    tensor = preprocess(pil_image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logit = model(tensor)
    prob_fake = torch.sigmoid(logit).item()
    label = "FAKE" if prob_fake > 0.5 else "REAL"
    confidence = prob_fake if prob_fake > 0.5 else 1.0 - prob_fake
    return {
        "label": label,
        "prob_fake": round(prob_fake, 4),
        "prob_real": round(1.0 - prob_fake, 4),
        "confidence": round(confidence, 4),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "device": str(DEVICE),
        "model_loaded": model is not None,
        "timm_available": TIMM_AVAILABLE,
    }


@app.post("/predict/video")
async def predict_video(file: UploadFile = File(...)):
    """Upload a video file; returns deepfake probability."""
    if model is None:
        raise HTTPException(503, "Model not loaded")

    suffix = Path(file.filename or "upload.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        frames = extract_frames(tmp_path, n=GRID_N)
        grid_img = build_thumbnail_grid(frames)
        result = run_inference(grid_img)
        result["frames_used"] = len(frames)
        result["grid_size"] = f"{GRID_ROWS}×{GRID_COLS}"
        return JSONResponse(result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))
    finally:
        os.unlink(tmp_path)


@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    """Upload a single image (or a thumbnail grid); returns deepfake probability."""
    if model is None:
        raise HTTPException(503, "Model not loaded")
    try:
        data = await file.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        result = run_inference(img)
        return JSONResponse(result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))


@app.post("/reload-model")
async def reload_model():
    """Hot-reload the .pth file without restarting the server."""
    try:
        load_model()
        return {"status": "reloaded", "path": MODEL_PATH}
    except Exception as e:
        raise HTTPException(500, str(e))