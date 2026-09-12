"""
NexusOCR Flat Configuration File (Compatibility Bridge).
Re-exports centralized constants, paths, and thresholds from nexusocr.config.
"""

from __future__ import annotations

import nexusocr.config as _cfg

# Base Paths
BASE_DIR = _cfg.BASE_DIR
DATA_DIR = _cfg.DATA_DIR
UPLOAD_DIR = _cfg.UPLOAD_DIR

# Image Rasterization DPI
BASE_RASTER_DPI = _cfg.BASE_RASTER_DPI

# Profiler & Trust Gates
TRUST_SCORE_NATIVE_THRESHOLD = _cfg.TRUST_SCORE_NATIVE_THRESHOLD

# Server Settings
SERVER_HOST = _cfg.SERVER_HOST
SERVER_PORT = _cfg.SERVER_PORT

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "UPLOAD_DIR",
    "BASE_RASTER_DPI",
    "TRUST_SCORE_NATIVE_THRESHOLD",
    "SERVER_HOST",
    "SERVER_PORT",
]
