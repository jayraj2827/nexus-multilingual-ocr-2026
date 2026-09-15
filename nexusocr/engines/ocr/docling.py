"""
Pillar 2: IBM Docling Layout & TableFormer Engine Adapter.
Provides deep document understanding, multi-column reading order, and table reconstruction.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, List

import fitz

from nexusocr.contracts.results import (
    DocumentResult,
    ExtractionSource,
    PageResult,
)
import nexusocr.config as config


class DoclingEngine:
    """IBM Docling Document Layout and Table Intelligence Engine."""

    def __init__(self) -> None:
        self._converter = None
        self._is_initialized = False

    def _init_converter(self) -> None:
        if not self._is_initialized:
            try:
                from docling.document_converter import DocumentConverter
                self._converter = DocumentConverter()
                self._is_initialized = True
                print("[NexusOCR] Docling DocumentConverter initialized successfully.")
            except Exception as e:
                print(f"[NexusOCR] Notice: Docling init deferred ({e}).")

    def is_available(self) -> bool:
        """Returns True if docling is installed and importable."""
        try:
            import docling
            return True
        except ImportError:
            return False

    def process_document(self, file_path: str) -> Optional[DocumentResult]:
        """
        Converts a document using IBM Docling's Layout & TableFormer models.
        """
        self._init_converter()
        if self._converter is None:
            return None

        start_time = time.perf_counter()
        file_name = Path(file_path).name

        try:
            conv_result = self._converter.convert(file_path)
            doc = conv_result.document
            full_markdown = doc.export_to_markdown()

            doc_fitz = fitz.open(file_path)
            total_pages = len(doc_fitz)
            page_results = []

            for page_idx in range(total_pages):
                page = doc_fitz[page_idx]
                pix = page.get_pixmap(dpi=config.BASE_RASTER_DPI)
                page_results.append(PageResult(
                    page_number=page_idx + 1,
                    width=pix.width,
                    height=pix.height,
                    is_digital=False,
                    trust_score=0.95,
                    markdown=full_markdown,
                    source=ExtractionSource.DOCLING_LAYOUT,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000.0
                ))
            doc_fitz.close()

            total_elapsed = (time.perf_counter() - start_time) * 1000.0

            return DocumentResult(
                file_name=file_name,
                total_pages=total_pages,
                pages=page_results,
                full_markdown=full_markdown,
                structured_json={"docling": True, "file": file_name},
                average_trust_score=0.95,
                total_execution_time_ms=total_elapsed
            )
        except Exception as err:
            print(f"[NexusOCR] Docling conversion exception: {err}")
            return None
