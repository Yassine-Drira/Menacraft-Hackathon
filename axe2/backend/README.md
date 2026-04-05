# VerifyAI Backend

FastAPI backend for the VerifyAI multimodal context verification system.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /verify` - Main verification endpoint
- `GET /docs` - Auto-generated Swagger UI

## Pipeline Stages

1. **Input Ingestion** - Validate file type, size, and caption
2. **Preprocessing** - Extract frames from videos, load images
3. **CLIP Early Exit Gate** - Quick semantic similarity check
4. **Deep AI Analysis** - BLIP captioning + spaCy NER (if not early exit)
5. **Consistency Comparator** - Cross-reference signals for inconsistencies
6. **Evidence Search** - Optional DuckDuckGo search for supporting evidence
7. **Output Generation** - Assemble final JSON response

## Models Used

- **CLIP** (openai/clip-vit-base-patch32) - Semantic similarity
- **BLIP** (Salesforce/blip-image-captioning-base) - Image captioning
- **spaCy** (en_core_web_sm) - Named entity recognition

All models are loaded at startup for optimal performance.