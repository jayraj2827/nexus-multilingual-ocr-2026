"""
NexusOCR Python SDK Client.
High-level programmatic entry point for document intelligence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import fitz

import nexusocr.config as config
from nexusocr.contracts.results import DocumentResult
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.features.vision.models import VisionAnalysisResult
from nexusocr.features.vision.service import VisionService
from nexusocr.processors.pdf import PDFProcessor


class NexusOCRClient:
    """Public Python SDK client for NexusOCR."""

    def __init__(self) -> None:
        self.ocr_service = DocumentOCRService()
        self.vision_service = VisionService()

    def process_document(self, file_path: str, max_pages: Optional[int] = None) -> DocumentResult:
        """Processes a PDF document using 2-Tier OCR Routing."""
        return self.ocr_service.process_pdf(file_path, max_pages=max_pages)

    def inspect_image(self, source: Union[str, Path, bytes]) -> VisionAnalysisResult:
        """Inspects an image and computes visual metrics."""
        return self.vision_service.inspect_image(source)

    def render_page_image(self, file_path: str, page_num: int, dpi: int = 150) -> bytes:
        """Renders a specific page of a PDF document as JPEG bytes."""
        with fitz.open(file_path) as doc:
            if page_num < 1 or page_num > len(doc):
                raise ValueError(f"Page number {page_num} out of bounds (1..{len(doc)})")
            page = doc[page_num - 1]
            return PDFProcessor.render_page_to_jpeg_bytes(page, dpi=dpi)

    def get_health(self) -> Dict[str, Any]:
        """Returns hardware telemetry and engine readiness."""
        try:
            import paddle
            cuda_avail = bool(paddle.is_compiled_with_cuda())
            gpu_cnt = paddle.device.cuda.device_count() if cuda_avail else 0
            gpu_name = paddle.device.cuda.get_device_name(0) if (cuda_avail and gpu_cnt > 0) else "CPU Only"
        except Exception:
            cuda_avail = False
            gpu_cnt = 0
            gpu_name = "CPU Only"

        return {
            "status": "healthy",
            "cuda_available": cuda_avail,
            "gpu_count": gpu_cnt,
            "gpu_name": gpu_name,
        }
