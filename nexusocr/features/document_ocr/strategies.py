"""
NexusOCR Document OCR Routing Strategies.
Encapsulates routing logic between Tier 1 (Digital Native) and Tier 2 (PaddleOCR GPU).
"""

from __future__ import annotations

from typing import Optional, Tuple
import fitz

from nexusocr.contracts.results import PageResult
from nexusocr.engines.ocr.pymupdf import extract_digital_page
from nexusocr.features.document_ocr.models import OCRPageDecision, OCRStrategyType
import nexusocr.config as config


class DocumentOCRStrategyRouter:
    """Decides and evaluates OCR extraction strategy per page."""

    def __init__(self, trust_threshold: float = config.TRUST_SCORE_NATIVE_THRESHOLD) -> None:
        self.trust_threshold = trust_threshold

    def evaluate_digital(self, page: fitz.Page, page_num: int) -> Tuple[float, Optional[PageResult]]:
        """Evaluates whether page can be extracted digitally via PyMuPDF."""
        return extract_digital_page(page, page_num)
