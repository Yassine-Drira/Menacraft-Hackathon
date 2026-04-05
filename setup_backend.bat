@echo off
echo Setting up VerifyAI backend with Python 3.10.11...
echo.

cd /d "C:\Users\Amen 53\Documents\web\Menacraft-Hackathon\backend"

echo Creating virtual environment...
py -3.10 -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Python 3.10 not found. Installing Python 3.10...
    winget install Python.Python.3.10 --accept-source-agreements
    py -3.10 -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing PyTorch (CPU version)...
pip install torch==2.1.2

echo Installing remaining dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo Downloading spaCy English model...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo ERROR: Failed to download spaCy model.
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo To start the backend server, run:
echo   cd backend
echo   venv\Scripts\activate
echo   python run.py
echo.
echo Or use uvicorn directly:
echo   uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
pause