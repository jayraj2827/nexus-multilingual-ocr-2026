"""
NexusOCR Features Package.
Contains domain-specific features: Document OCR, Layout, Vision, Speech, Translation.
"""

from __future__ import annotations

from nexusocr.features.document_ocr import DocumentOCRService, DocumentOCRStage
from nexusocr.features.layout import LayoutService, LayoutStage
from nexusocr.features.vision import VisionService, VisionStage
from nexusocr.features.speech import SpeechService, SpeechStage
from nexusocr.features.translation import TranslationService, TranslationStage

__all__ = [
    "DocumentOCRService",
    "DocumentOCRStage",
    "LayoutService",
    "LayoutStage",
    "VisionService",
    "VisionStage",
    "SpeechService",
    "SpeechStage",
    "TranslationService",
    "TranslationStage",
]
