"""
NexusOCR Flat Configuration File (KISS & Developer-Friendly).
Centralized constants, endpoints, and thresholds.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Image Rasterization DPI (used for scanned page rendering)
BASE_RASTER_DPI = 150

# Profiler & Trust Gates
# Pages with native text score >= threshold go through PyMuPDF (<40ms)
# Pages below threshold fall through to PaddleOCR GPU
TRUST_SCORE_NATIVE_THRESHOLD = 0.85

# Server Settings
SERVER_HOST = "127.0.0.1"
SERVER_PORT = int(os.getenv("PORT", 8000))
