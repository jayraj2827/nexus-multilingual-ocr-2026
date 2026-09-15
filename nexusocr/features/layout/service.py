"""
NexusOCR Layout Feature Service.
Reconstructs reading order, multi-column blocks, and table structures.
"""

from __future__ import annotations

from typing import List, Optional
import fitz

from nexusocr.contracts.results import DocumentResult
from nexusocr.engines.ocr.docling import DoclingEngine
from nexusocr.features.layout.models import LayoutAnalysisResult, LayoutElement


class LayoutService:
    """Provides layout structure analysis and table intelligence."""

    def __init__(self, docling_engine: Optional[DoclingEngine] = None) -> None:
        self.docling_engine: DoclingEngine = docling_engine or DoclingEngine()

    def analyze_document_layout(self, file_path: str) -> Optional[DocumentResult]:
        """Runs Docling layout & TableFormer if available on the document."""
        if self.docling_engine.is_available():
            return self.docling_engine.process_document(file_path)
        return None
