"""
Configuration parameters for NexusOCR.
Following KISS principles: flat, explicit, and easy to modify.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
BENCHMARK_DIR = DATA_DIR / "benchmark_suite"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Create directories if they don't exist
for d in [DATA_DIR, MODELS_DIR, BENCHMARK_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Gating Thresholds
TRUST_SCORE_NATIVE_THRESHOLD = 0.90   # >= 0.90 extracts native PDF text directly
LAYOUT_CONFIDENCE_THRESHOLD = 0.70    # < 0.70 escalates from PP-DocLayout-S to PP-DocLayout-M
CONFIDENCE_ACCEPT_THRESHOLD = 0.80    # >= 0.80 accepts OCR result without retry
CONFIDENCE_RETRY_THRESHOLD = 0.60     # < 0.80 triggers Fallback A (OpenCV retry)
                                      # < 0.60 (or failed HW) triggers Fallback B (Terminal VLM)

# DPI Settings
BASE_RASTER_DPI = 200                 # Lightweight baseline rendering
HIGH_RES_ZOOM_DPI = 350               # Detail re-render for small/dense crops

# Decoupled VLM Endpoint (Fallback B)
# Can be overridden via environment variables or local mock
VLM_SERVICE_URL = "http://localhost:8000/v1/vlm/extract"
VLM_TIMEOUT_SECONDS = 15.0

# Concurrency
MAX_OCR_WORKERS = 2                   # Safe for 4 vCPU / 8 GB RAM deployment
