"""
NexusOCR Unified Pipeline Orchestrator (Compatibility Bridge).
Fast 2-Tier Architecture routing digital pages to PyMuPDF and scanned pages to PaddleOCR GPU.
Re-exports NexusOCRPipeline delegating to nexusocr.features.document_ocr.service.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

from nexusocr.contracts.results import DocumentResult, ExtractionSource, PageResult
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.logging import log

# Ensure UTF-8 output encoding
os.environ["PYTHONUNBUFFERED"] = "1"
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class NexusOCRPipeline(DocumentOCRService):
    """End-to-End Document Intelligence Pipeline (Preserving existing interface)."""

    def __init__(self) -> None:
        log("[NexusOCR] Initializing NexusOCR Pipeline...")
        super().__init__()
        log("[NexusOCR] Pipeline ready.")


__all__ = [
    "NexusOCRPipeline",
    "log",
    "DocumentResult",
    "PageResult",
    "ExtractionSource",
]
