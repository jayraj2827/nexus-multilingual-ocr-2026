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


def detect_hardware() -> dict:
    """
    Detects underlying system hardware (AMD/Intel CPU, NVIDIA CUDA, AMD ROCm).
    Provides consistent hardware telemetry without hardcoding NVIDIA-specific assumptions.
    """
    import platform
    cpu_str = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "") or platform.machine()
    is_amd = "AMD" in cpu_str.upper() or "AUTHENTICAMD" in cpu_str.upper()

    cuda_available = False
    gpu_count = 0
    device_name = f"AMD CPU ({cpu_str})" if is_amd else f"CPU ({cpu_str})"
    device_type = "cpu"

    try:
        import paddle
        if paddle.is_compiled_with_cuda():
            gpu_count = paddle.device.cuda.device_count()
            if gpu_count > 0:
                cuda_available = True
                device_type = "gpu"
                device_name = f"NVIDIA {paddle.device.cuda.get_device_name(0)}"
        elif hasattr(paddle.device, "is_compiled_with_rocm") and paddle.device.is_compiled_with_rocm():
            device_type = "gpu"
            device_name = "AMD ROCm GPU"
    except Exception:
        pass

    return {
        "device_type": device_type,
        "device_name": device_name,
        "cuda_available": cuda_available,
        "gpu_count": gpu_count,
        "is_amd_hardware": is_amd,
        "platform_processor": cpu_str,
    }
