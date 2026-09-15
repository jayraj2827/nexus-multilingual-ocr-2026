"""
NexusOCR Document & Image Intelligence Pipeline Stage.
Integrates DocumentOCRService with the centralized PipelineRunner.
"""

from __future__ import annotations

from typing import Optional

from nexusocr.contracts.formats import FormatResolver
from nexusocr.contracts.results import DocumentResult
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.stage import PipelineStage


class DocumentOCRStage(PipelineStage):
    """Pipeline stage executing multi-format document and image OCR."""

    def __init__(
        self,
        service: Optional[DocumentOCRService] = None,
        name: str = "DocumentOCRStage",
        enabled: bool = True
    ) -> None:
        super().__init__(name=name, enabled=enabled)
        self.service: DocumentOCRService = service or DocumentOCRService()

    def can_handle(self, context: ProcessingContext) -> bool:
        return (
            super().can_handle(context)
            and context.options.enable_ocr
            and FormatResolver.is_supported(context.file_path)
        )

    def process(self, context: ProcessingContext) -> DocumentResult:
        result = self.service.process_document(
            file_path=context.file_path,
            options=context.options
        )
        context.document_result = result
        return result
