import subprocess
import time
import sys
import os

def start_platform():
    print("=================================================================")
    print("      NETRADEEP: City-Wide ANPR Intelligence Platform           ")
    print("=================================================================")
    print("  [1] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    
    backend_cmd = [sys.executable, "run_backend.py"]
    backend_proc = subprocess.Popen(backend_cmd)
    
    time.sleep(2)
    print("  [2] Starting Vite Frontend on http://localhost:5173 ...")
    
    frontend_cmd = ["npm", "run", "dev", "--prefix", "frontend"]
    frontend_proc = subprocess.Popen(frontend_cmd, shell=True)

    print("\n  Dashboard URL: http://localhost:5173")
    print("  Backend Docs:  http://127.0.0.1:8000/docs")
    print("  WebSocket:     ws://127.0.0.1:8000/ws/live")
    print("=================================================================")
    print("  Press Ctrl+C to terminate both servers.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down platform...")
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    start_platform()
