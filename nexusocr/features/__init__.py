"""
NexusOCR Features Package.
Contains domain-specific features: Document OCR, Layout, Vision, Speech, Translation.
"""

from __future__ import annotations

from nexusocr.features.document_ocr import DocumentOCRService, DocumentOCRStage, FormDataExtractor
from nexusocr.features.layout import LayoutService, LayoutStage
from nexusocr.features.vision import VisionService, VisionStage
from nexusocr.features.translation import TranslationService, TranslationStage
from nexusocr.features.batch import BatchDocumentService

__all__ = [
    "DocumentOCRService",
    "DocumentOCRStage",
    "FormDataExtractor",
    "LayoutService",
    "LayoutStage",
    "VisionService",
    "VisionStage",
    "TranslationService",
    "TranslationStage",
    "BatchDocumentService",
]
