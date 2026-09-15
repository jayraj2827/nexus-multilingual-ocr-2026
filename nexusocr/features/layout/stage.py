"""
NexusOCR Layout Pipeline Stage.
"""

from __future__ import annotations

from typing import Optional

from nexusocr.features.layout.service import LayoutService
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.stage import PipelineStage


class LayoutStage(PipelineStage):
    """Pipeline stage executing deep document layout analysis."""

    def __init__(
        self,
        service: Optional[LayoutService] = None,
        name: str = "LayoutStage",
        enabled: bool = True
    ) -> None:
        super().__init__(name=name, enabled=enabled)
        self.service: LayoutService = service or LayoutService()

    def can_handle(self, context: ProcessingContext) -> bool:
        return (
            super().can_handle(context)
            and context.options.enable_layout
            and self.service.docling_engine.is_available()
        )

    def process(self, context: ProcessingContext) -> Optional[object]:
        result = self.service.analyze_document_layout(context.file_path)
        if result is not None:
            context.artifacts["docling_layout"] = result
        return result
