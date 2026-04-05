"""
OCR Screenshot Uploader for VerifyAI

Usage:
  1. Install prerequisites in your backend venv:
       pip install pillow pytesseract requests
  2. Install Tesseract OCR engine on Windows:
       https://github.com/tesseract-ocr/tesseract
  3. Run the script:
       python ocr_screenshot_uploader.py
  4. Use Windows screenshot copy (Win+Shift+S) or Print Screen to copy an image to clipboard.
  5. The script detects the clipboard image, extracts text, and POSTs it to your backend.

Notes:
- The backend must be running at BACKEND_URL.
- The script uploads the screenshot image and sends extracted text as caption.
- If the clipboard image does not change, it will not resend the same screenshot.
"""

import hashlib
import io
import sys
import time

import pytesseract
import requests
from PIL import Image, ImageGrab, ImageOps

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BACKEND_URL = "http://localhost:8000/verify"
POLL_INTERVAL = 1.5
SAVE_DEBUG_IMAGES = False
SEARCH_ENABLED = False


def get_clipboard_image() -> "Image.Image | None":
    """Return an image from the clipboard if available."""
    try:
        img = ImageGrab.grabclipboard()
    except Exception as exc:
        print(f"[ERROR] Clipboard read failed: {exc}")
        return None

    if isinstance(img, Image.Image):
        return img
    return None


def hash_image(image: Image.Image) -> str:
    """Compute a stable hash for the clipboard image."""
    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        return hashlib.sha256(buffer.getvalue()).hexdigest()


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Improve OCR accuracy by converting to grayscale and applying contrast."""
    gray = ImageOps.grayscale(image)
    enhanced = ImageOps.autocontrast(gray)
    return enhanced


def extract_caption_text(image: Image.Image) -> str:
    """Run OCR on the screenshot and return cleaned text."""
    ocr_image = preprocess_for_ocr(image)
    raw_text = pytesseract.image_to_string(ocr_image, lang="eng")
    cleaned = "\n".join(line.strip() for line in raw_text.splitlines() if line.strip())
    return cleaned


def send_to_backend(image: Image.Image, caption: str) -> None:
    """Send the screenshot and extracted caption to VerifyAI backend."""
    if not caption:
        print("[WARN] OCR extracted no text. Sending the screenshot anyway.")

    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        buffer.seek(0)

        files = {
            "media": ("screenshot.png", buffer, "image/png")
        }
        data = {
            "caption": caption,
            "search_enabled": str(SEARCH_ENABLED).lower()
        }

        print("[INFO] Sending screenshot and caption to backend...")
        response = requests.post(BACKEND_URL, files=files, data=data, timeout=60)

    if response.ok:
        print("[OK] Backend returned:")
        print(response.text)
    else:
        print(f"[ERROR] Backend request failed: {response.status_code}")
        print(response.text)


def main() -> int:
    print("OCR Screenshot Uploader for VerifyAI")
    print(f"Watching clipboard for images. Backend URL: {BACKEND_URL}")
    print("Use Win+Shift+S or Print Screen to copy a screenshot to clipboard.")
    last_hash = None

    while True:
        image = get_clipboard_image()
        if image is None:
            time.sleep(POLL_INTERVAL)
            continue

        current_hash = hash_image(image)
        if current_hash == last_hash:
            time.sleep(POLL_INTERVAL)
            continue

        last_hash = current_hash
        caption = extract_caption_text(image)

        print("\n--- New screenshot detected ---")
        print(f"Extracted caption:\n{caption or '[no text]'}")

        if SAVE_DEBUG_IMAGES:
            filename = f"screenshot_{int(time.time())}.png"
            image.save(filename)
            print(f"Saved debug screenshot to {filename}")

        try:
            send_to_backend(image, caption)
        except Exception as exc:
            print(f"[ERROR] Failed to send to backend: {exc}")

        print("Waiting for next screenshot...\n")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
