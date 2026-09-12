"""
NexusOCR Engine Adapters Package.
Contains wrappers and adapters for external OCR, vision, speech, and translation engines.
"""

from __future__ import annotations

from nexusocr.engines.ocr.base import BaseOCREngine
from nexusocr.engines.ocr.pymupdf import PyMuPDFEngine, extract_digital_page
from nexusocr.engines.ocr.paddleocr import PaddleOCREngine
from nexusocr.engines.ocr.docling import DoclingEngine
from nexusocr.engines.vision.base import BaseVisionEngine, DefaultVisionEngine
from nexusocr.engines.speech.base import BaseSpeechEngine, DefaultSpeechEngine
from nexusocr.engines.translation.base import BaseTranslationEngine, DefaultTranslationEngine

__all__ = [
    "BaseOCREngine",
    "PyMuPDFEngine",
    "extract_digital_page",
    "PaddleOCREngine",
    "DoclingEngine",
    "BaseVisionEngine",
    "DefaultVisionEngine",
    "BaseSpeechEngine",
    "DefaultSpeechEngine",
    "BaseTranslationEngine",
    "DefaultTranslationEngine",
]
