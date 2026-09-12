"""
NexusOCR Centralized Configuration.
Maintains constants, paths, thresholds, and server settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Base Paths (Project Root is parent of nexusocr package)
PACKAGE_DIR: Path = Path(__file__).resolve().parent
BASE_DIR: Path = PACKAGE_DIR.parent
DATA_DIR: Path = BASE_DIR / "data"
UPLOAD_DIR: Path = DATA_DIR / "uploads"
FRONTEND_DIR: Path = BASE_DIR / "frontend"
FIXTURES_DIR: Path = BASE_DIR / "tests" / "fixtures"

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Image Rasterization DPI (used for scanned page rendering)
BASE_RASTER_DPI: int = 150

# Profiler & Trust Gates
# Pages with native text score >= threshold go through PyMuPDF (<40ms)
# Pages below threshold fall through to PaddleOCR GPU
TRUST_SCORE_NATIVE_THRESHOLD: float = 0.85

# Server Settings
SERVER_HOST: str = "127.0.0.1"
SERVER_PORT: int = int(os.getenv("PORT", 8000))
