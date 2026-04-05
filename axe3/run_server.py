#!/usr/bin/env python
"""
Simple script to run the FastAPI server without uvicorn module import issues.
"""
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    print("Starting ClipTrust - Axe 3 Source Credibility Engine...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,
        log_level="info"
    )
