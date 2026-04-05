# VerifyAI - Quick Start Guide

## ✅ Automated Setup (Recommended)

### 1. Run Setup Script
From project root:
```bash
setup_backend.bat
```
This installs everything automatically (Python 3.10, venv, all deps, spaCy model).

### 2. Start Backend (Terminal 1)
```bash
cd backend
venv\Scripts\activate
python run.py
```
✅ Server starts: http://localhost:8000

### 3. Start Frontend (Terminal 2)
```bash
cd frontend
npm install
npm run dev
```
✅ App opens: http://localhost:5173

---

## 🔧 Manual Setup (If Needed)

### Backend
```bash
cd backend
py -3.10 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install torch==2.1.2
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Start Backend:**
```bash
cd backend
venv\Scripts\activate
python run.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📋 Alternative Backend Commands

If `python run.py` doesn't work:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ Verify Installation

```bash
cd backend
venv\Scripts\activate
python -c "import fastapi, torch, transformers, cv2, spacy; print('✅ All dependencies working!')"
```

---

## 🎯 API Endpoints

- **Main URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Verify Endpoint**: POST http://localhost:8000/verify
  - Parameters: `file` (image/video), `caption` (text), `search_enabled` (bool)
  - Response: JSON with verdict, score, flags, analysis

---

## 📱 Access App

- **Frontend**: http://localhost:5173
- **Upload file** → **Enter caption** → **Click Verify** → **View results**

---

## ❌ Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run: `venv\Scripts\activate` then retry |
| `Port 8000 already in use` | Change port: `uvicorn main:app --port 8001` |
| `Model download fails` | Check internet, then: `python -m spacy download en_core_web_sm` |
| Frontend blank | Check http://localhost:8000/docs - if API works, refresh frontend at 5173 |

---

## 📦 Dependencies Installed

**Backend (Python):**
- torch==2.1.2 (ML framework)
- transformers==4.35.2 (CLIP, BLIP models)
- fastapi==0.104.1 (Web API)
- uvicorn==0.23.2 (ASGI server)
- opencv-python-headless==4.8.1.78 (Video processing)
- spacy==3.7.2 (NLP)
- pillow==10.0.1 (Image handling)
- duckduckgo-search==4.4.3 (Evidence search)

**Frontend (Node.js):**
- react@18.3.1
- vite@5.4.1

---

## 🚀 Next Steps

1. Test with sample image/video
2. Check API at http://localhost:8000/docs
3. Customize models if needed
4. Deploy to cloud when ready