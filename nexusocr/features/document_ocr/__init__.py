"""
NexusOCR Document OCR Feature Package.
"""

from __future__ import annotations

from nexusocr.features.document_ocr.models import OCRPageDecision, OCRStrategyType
from nexusocr.features.document_ocr.strategies import DocumentOCRStrategyRouter
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.features.document_ocr.stage import DocumentOCRStage
from nexusocr.features.document_ocr.forms import FormDataExtractor

__all__ = [
    "OCRPageDecision",
    "OCRStrategyType",
    "DocumentOCRStrategyRouter",
    "DocumentOCRService",
    "DocumentOCRStage",
    "FormDataExtractor",
]
