"""
NexusOCR FastAPI Application Server (Compatibility Bridge).
Exposes the modern web UI and REST endpoints for document intelligence.
"""

from __future__ import annotations

import sys
from pathlib import Path

import config
from nexusocr.interfaces.api.app import app
from pipeline import NexusOCRPipeline

# Ensure UTF-8 output encoding
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Initialize pipeline for backward compatibility
pipeline = NexusOCRPipeline()

# Paths
BASE_DIR: Path = config.BASE_DIR
frontend_dir: Path = BASE_DIR / "frontend"
fixtures_dir: Path = BASE_DIR / "tests" / "fixtures"

if __name__ == "__main__":
    import uvicorn
    port = config.SERVER_PORT
    print(f"Starting NexusOCR server on http://127.0.0.1:{port} ...", flush=True)
    uvicorn.run("app:app", host=config.SERVER_HOST, port=port, reload=True)
