"""
NexusOCR: Adaptive Multilingual Document Intelligence Engine.
Hybrid feature-oriented pipeline architecture.
"""

from __future__ import annotations

from nexusocr.contracts import (
    BoundingBox,
    DocumentInput,
    DocumentResult,
    ExtractedRegion,
    ExtractionSource,
    PageResult,
    ProcessingOptions,
    StageResult,
    StageStatus,
    TableStructure,
)
from nexusocr.features.document_ocr import DocumentOCRService
from nexusocr.interfaces.sdk import NexusOCRClient
from nexusocr.pipeline import PipelineRunner, PipelineStage, ProcessingContext

# High-level pipeline class preserving backward compatibility
NexusOCRPipeline = DocumentOCRService

__all__ = [
    "NexusOCRPipeline",
    "NexusOCRClient",
    "DocumentOCRService",
    "PipelineRunner",
    "PipelineStage",
    "ProcessingContext",
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
]
