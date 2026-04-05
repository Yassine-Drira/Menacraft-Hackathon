# VerifyAI Setup Guide

## Overview

This guide will help you set up and run the VerifyAI contextual consistency verification system. The system has been fully implemented according to the PRD specifications.

## Prerequisites

- **Python 3.10.11** with pip (specifically this version for compatibility)
- **Node.js 16+** with npm
- **Git** for version control
- **At least 4GB RAM** (recommended for ML models)
- **Stable internet connection** (for model downloads and evidence search)

## Quick Setup

### 1. Install Python 3.10.11

✅ **Already installed!** Python 3.10.11 was successfully installed via winget.

### 2. Run Automated Setup

Simply double-click the `setup_backend.bat` file in the project root, or run:

```bash
# Navigate to project root
cd "C:\Users\Amen 53\Documents\web\Menacraft-Hackathon"

# Run the setup script
setup_backend.bat
```

This will automatically:
- Create a Python 3.10.11 virtual environment
- Install all dependencies
- Download the spaCy language model

### 3. Alternative Manual Setup

If you prefer manual setup:

```bash
# Navigate to backend
cd backend

# Create virtual environment with Python 3.10
py -3.10 -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Validate installation (optional)
python validate_pipeline.py
```

### 3. Frontend Setup

```bash
# Navigate to frontend (in new terminal)
cd frontend

# Install Node.js dependencies
npm install

# Build and validate (optional)
npm run build
```

### 4. Start Services

**Backend (Terminal 1):**
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```

### 5. Access Application

- **Frontend UI**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000

## Next Steps

1. **Test with sample data** - Try different images/videos and captions
2. **Review API documentation** - Visit `/docs` for detailed endpoint info
3. **Customize models** - Modify pipeline for different use cases
4. **Add authentication** - Implement user management if needed
5. **Deploy to production** - Set up cloud hosting and CI/CD

## Troubleshooting

### Common Issues

**"ModuleNotFoundError"**
- Ensure virtual environment is activated: `venv\Scripts\activate`
- Reinstall requirements: `pip install -r requirements.txt`

**"Model download failed"**
- Check internet connection
- Models download automatically on first use
- May take 5-10 minutes for large models

**"Port already in use"**
- Kill existing processes or change ports

**"GCC compiler issues"**
- Python 3.10.11 includes compatible compilers for all dependencies

### Performance Optimization

**For better performance:**
- Use GPU if available (CUDA)
- Increase system RAM to 8GB+
- Use SSD storage for model cache
- Close other memory-intensive applications

## Detailed Setup

### Backend Dependencies

The `requirements.txt` includes (Python 3.10.10 compatible versions):
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.23.2` - ASGI server
- `python-multipart==0.0.6` - File upload handling
- `transformers==4.35.2` - Hugging Face models (CLIP, BLIP)
- `torch==2.1.2` - PyTorch for ML models
- `spacy==3.7.2` - NLP processing
- `opencv-python-headless==4.8.1.78` - Video processing
- `Pillow==10.0.1` - Image processing
- `duckduckgo-search==4.4.3` - Evidence search
- `numpy==1.24.3` - Numerical computations
- `pydantic==2.5.0` - Data validation

### Model Downloads

The system automatically downloads required ML models on first run:
- **CLIP**: `openai/clip-vit-base-patch32` (~600MB)
- **BLIP**: `Salesforce/blip-image-captioning-base` (~1.2GB)
- **spaCy**: `en_core_web_sm` (~12MB)

First startup may take several minutes for model downloads.

### Environment Configuration

Create `.env` file in backend directory (optional):
```env
API_URL=http://localhost:8000
MODEL_CACHE_DIR=./models/cache
```

## Testing the System

### 1. API Test
```bash
# Test with curl
curl -X POST "http://localhost:8000/verify" \
  -F "file=@test_image.jpg" \
  -F "caption=A person standing in New York City" \
  -F "search_enabled=true"
```

### 2. Frontend Test
1. Open http://localhost:5173
2. Upload an image or video
3. Enter a caption
4. Toggle evidence search if desired
5. Click "Verify Content"
6. View results

### 3. Pipeline Validation
```bash
cd backend
python validate_pipeline.py
```

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'fastapi'"**
- Ensure virtual environment is activated: `venv\Scripts\activate`
- Reinstall requirements: `pip install -r requirements.txt`

**"Model download failed"**
- Check internet connection
- Models download automatically on first use
- May take 5-10 minutes for large models

**"CUDA out of memory"**
- System falls back to CPU if GPU memory insufficient
- Reduce batch sizes in pipeline if needed

**"Port already in use"**
- Kill existing processes: `netstat -ano | findstr :8000`
- Change ports in startup commands

### Performance Optimization

**For better performance:**
- Use GPU if available (CUDA)
- Increase system RAM to 8GB+
- Use SSD storage for model cache
- Close other memory-intensive applications

**For development:**
- Use `--reload` flag for auto-restart on code changes
- Check logs in terminal for debugging info

## File Structure

```
Menacraft-Hackathon/
├── README.md              # PRD and specifications
├── SETUP.md              # This setup guide
├── .gitignore            # Git ignore rules
├── backend/
│   ├── main.py           # FastAPI application
│   ├── requirements.txt  # Python dependencies
│   ├── validate_pipeline.py  # Validation script
│   ├── models/
│   │   └── loader.py     # ML model management
│   └── pipeline/         # AI processing pipeline
│       ├── ingest.py     # Input validation
│       ├── preprocess.py # Media preprocessing
│       ├── clip_gate.py  # Early exit logic
│       ├── blip_captioner.py # Image captioning
│       ├── ner_extractor.py  # Entity extraction
│       ├── comparator.py  # Consistency analysis
│       ├── evidence_search.py # Web search
│       └── output_builder.py  # Response formatting
└── frontend/
    ├── package.json      # Node.js dependencies
    ├── vite.config.js    # Vite configuration
    ├── index.html        # HTML template
    ├── src/
    │   ├── App.jsx       # Main React app
    │   ├── main.jsx      # React entry point
    │   ├── styles.css    # Global styles
    │   └── components/   # React components
    │       ├── UploadForm.jsx
    │       ├── LoadingState.jsx
    │       ├── VerdictHeader.jsx
    │       ├── FlagChips.jsx
    │       ├── Explanation.jsx
    │       ├── AnalysisDetail.jsx
    │       └── Evidence.jsx
    └── public/
        └── vite.svg
```

## Next Steps

1. **Test with sample data** - Try different images/videos and captions
2. **Review API documentation** - Visit `/docs` for detailed endpoint info
3. **Customize models** - Modify pipeline for different use cases
4. **Add authentication** - Implement user management if needed
5. **Deploy to production** - Set up cloud hosting and CI/CD

## Support

- Check the README.md for detailed specifications
- Review code comments for implementation details
- Test individual pipeline stages for debugging

The system is now ready for use! 🚀