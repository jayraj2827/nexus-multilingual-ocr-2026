"""
Pillar 3: PaddleOCR v3.7 Engine (Compatibility Bridge).
Re-exports PaddleOCREngine and _stub_modelscope from nexusocr.engines.ocr.paddleocr.
"""

from __future__ import annotations

from nexusocr.engines.ocr.paddleocr import (
    PaddleOCREngine,
    _stub_modelscope,
)

__all__ = [
    "PaddleOCREngine",
    "_stub_modelscope",
]
