"""
NexusOCR FastAPI Application Factory.
"""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import nexusocr.config as config
from nexusocr.interfaces.api.routes import router

# Ensure UTF-8 output encoding
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def create_app() -> FastAPI:
    """Builds and configures the FastAPI application instance."""
    app_instance = FastAPI(title="NexusOCR Engine", version="2.0.0")

    # Mount static frontend
    frontend_dir = config.FRONTEND_DIR
    if frontend_dir.exists():
        app_instance.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # Register API routes
    app_instance.include_router(router)

    return app_instance


app: FastAPI = create_app()
