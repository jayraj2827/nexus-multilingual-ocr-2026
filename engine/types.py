"""
NexusOCR Core Type Definitions (Compatibility Bridge).
Re-exports Pydantic schemas from nexusocr.contracts.results.
"""

from __future__ import annotations

from nexusocr.contracts.results import (
    ExtractionSource,
    BoundingBox,
    ExtractedRegion,
    TableStructure,
    PageResult,
    DocumentResult,
)

__all__ = [
    "ExtractionSource",
    "BoundingBox",
    "ExtractedRegion",
    "TableStructure",
    "PageResult",
    "DocumentResult",
]
