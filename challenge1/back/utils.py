import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms

def extract_frames(video_path, num_frames=8, face_size=112):
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        raise ValueError(f"Cannot read video or video is empty: {video_path}")
    
    frames = []
    # Pick frames evenly across the video duration
    indices = np.linspace(0, total - 1, num_frames, dtype=int)
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success: continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (face_size, face_size))
        frames.append(frame)
    cap.release()
    return frames

def build_thumbnail_grid(frames, grid_rows=2):
    grid_cols = int(np.ceil(len(frames) / grid_rows))
    # Pad with black frames if necessary
    while len(frames) < grid_rows * grid_cols:
        frames.append(np.zeros_like(frames[0]))
    
    rows = []
    for r in range(grid_rows):
        row = frames[r * grid_cols : (r + 1) * grid_cols]
        rows.append(np.concatenate(row, axis=1))
    return Image.fromarray(np.concatenate(rows, axis=0))

def apply_fixed_mask(grid, mask_ratio=0.08):
    arr = np.array(grid)
    mh, mw = int(arr.shape[0] * mask_ratio), int(arr.shape[1] * mask_ratio)
    arr[:mh, :mw] = 0 # Corner masking used in your notebook logic
    return Image.fromarray(arr)

def get_inference_transform(grid_rows=2, grid_cols=4, face_size=112):
    return transforms.Compose([
        transforms.Resize((grid_rows * face_size, grid_cols * face_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])