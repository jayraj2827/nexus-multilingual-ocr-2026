"""
NexusOCR Batch Document Processing Service.
Coordinates multi-document processing queues with partial failure isolation and summary analytics.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from nexusocr.contracts.input import ProcessingOptions
from nexusocr.contracts.results import DocumentResult
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.logging import log


class BatchFailure(BaseModel):
    file_path: str
    file_name: str
    error: str
    elapsed_ms: str = "0.0"


class BatchResult(BaseModel):
    total_items: int = 0
    successful_count: int = 0
    failed_count: int = 0
    total_pages_processed: int = 0
    total_execution_time_ms: float = 0.0
    results: List[DocumentResult] = Field(default_factory=list)
    failures: List[BatchFailure] = Field(default_factory=list)


class BatchDocumentService:
    """Processes collections of documents and images with graceful error isolation."""

    def __init__(self, ocr_service: Optional[DocumentOCRService] = None) -> None:
        self.ocr_service: DocumentOCRService = ocr_service or DocumentOCRService()

    def process_batch(
        self,
        file_paths: List[str],
        options: Optional[ProcessingOptions] = None
    ) -> BatchResult:
        """
        Executes document intelligence over a list of document or image files.
        Guarantees that a failure in one document does not fail the entire batch.
        """
        start_time = time.perf_counter()
        successful_results: List[DocumentResult] = []
        failed_files: List[BatchFailure] = []
        total_pages = 0

        log(f"\n[NexusOCR] [Batch] Starting batch processing for {len(file_paths)} item(s)...")

        for idx, path_str in enumerate(file_paths):
            item_start = time.perf_counter()
            file_name = Path(path_str).name
            log(f"[NexusOCR] [Batch] Processing item {idx+1}/{len(file_paths)}: '{file_name}'...")

            try:
                result = self.ocr_service.process_document(path_str, options=options)
                successful_results.append(result)
                total_pages += result.total_pages
                elapsed_item = (time.perf_counter() - item_start) * 1000.0
                log(f"[NexusOCR] [Batch] Item {idx+1} completed in {elapsed_item:.1f}ms ({result.total_pages} page(s))")

            except Exception as exc:
                elapsed_item = (time.perf_counter() - item_start) * 1000.0
                log(f"[NexusOCR] [Batch Warning] Item {idx+1} failed: {exc}")
                failed_files.append(BatchFailure(
                    file_path=path_str,
                    file_name=file_name,
                    error=str(exc),
                    elapsed_ms=f"{elapsed_item:.1f}",
                ))

        total_ms = (time.perf_counter() - start_time) * 1000.0
        log(f"[NexusOCR] [Batch Complete] {len(successful_results)} succeeded, {len(failed_files)} failed in {total_ms:.1f}ms\n")

        return BatchResult(
            total_items=len(file_paths),
            successful_count=len(successful_results),
            failed_count=len(failed_files),
            total_pages_processed=total_pages,
            total_execution_time_ms=total_ms,
            results=successful_results,
            failures=failed_files,
        )
