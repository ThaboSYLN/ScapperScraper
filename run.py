import os
import sys
import uvicorn

# Force UTF-8 across the board — prevents Windows cp1252 encoding errors
os.environ["PYTHONUTF8"] = "1"

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,           # Auto-restart on file save (dev only)
        log_level="info",
    )