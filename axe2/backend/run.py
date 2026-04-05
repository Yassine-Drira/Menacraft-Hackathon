#!/usr/bin/env python3
"""
Startup script for VerifyAI backend.
Run with: python run.py
"""

import subprocess
import sys

if __name__ == "__main__":
    # Run FastAPI as a module to support relative imports
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd="."
    )
