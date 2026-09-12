"""
Pillar 1: Digital PDF & Fast Native Text/Table Extractor (Compatibility Bridge).
Re-exports extract_digital_page from nexusocr.engines.ocr.pymupdf.
"""

from __future__ import annotations

from typing import Optional, Tuple
import fitz

from engine.types import (
    PageResult,
    ExtractedRegion,
    BoundingBox,
    TableStructure,
    ExtractionSource,
)
from nexusocr.engines.ocr.pymupdf import extract_digital_page

__all__ = [
    "extract_digital_page",
    "PageResult",
    "ExtractedRegion",
    "BoundingBox",
    "TableStructure",
    "ExtractionSource",
]
