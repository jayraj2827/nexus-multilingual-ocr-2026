"""
NexusOCR Data Contracts Package.
Re-exports all shared data structures for seamless importing.
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
from nexusocr.contracts.input import (
    DocumentInput,
    ProcessingOptions,
    StageResult,
    StageStatus,
)
from nexusocr.contracts.output import (
    PipelineSummary,
    format_document_json,
)
from nexusocr.contracts.formats import (
    FormatCategory,
    ExtractionMode,
    FormatCapability,
    FormatResolver,
)

__all__ = [
    "ExtractionSource",
    "BoundingBox",
    "ExtractedRegion",
    "TableStructure",
    "PageResult",
    "DocumentResult",
    "DocumentInput",
    "ProcessingOptions",
    "StageResult",
    "StageStatus",
    "PipelineSummary",
    "format_document_json",
    "FormatCategory",
    "ExtractionMode",
    "FormatCapability",
    "FormatResolver",
]
