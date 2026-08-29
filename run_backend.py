import uvicorn
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath("backend"))

if __name__ == "__main__":
    print("=================================================================")
    print("  Starting City-Wide ANPR Intelligence Platform Backend (FastAPI)")
    print("  Swagger UI Docs: http://127.0.0.1:8000/docs")
    print("  WebSocket Live Stream: ws://127.0.0.1:8000/ws/live")
    print("=================================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
