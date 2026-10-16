import os
import sys
import uvicorn

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 60)
    print(" [>] Starting Smart Travel Planner Locally")
    print(f" [>] Open your browser at: http://localhost:{port}")
    print("=" * 60)
    uvicorn.run("api.index:app", host="127.0.0.1", port=port, reload=True)
