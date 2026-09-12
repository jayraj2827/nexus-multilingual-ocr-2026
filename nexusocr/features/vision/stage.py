"""
NexusOCR Vision Pipeline Stage.
"""

from __future__ import annotations

from typing import Optional

from nexusocr.features.vision.models import VisionAnalysisResult
from nexusocr.features.vision.service import VisionService
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.stage import PipelineStage


class VisionStage(PipelineStage):
    """Pipeline stage executing visual inspection for image files."""

    def __init__(
        self,
        service: Optional[VisionService] = None,
        name: str = "VisionStage",
        enabled: bool = True
    ) -> None:
        super().__init__(name=name, enabled=enabled)
        self.service: VisionService = service or VisionService()

    def can_handle(self, context: ProcessingContext) -> bool:
        ext = context.file_path.lower()
        is_image = ext.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"))
        return super().can_handle(context) and is_image

    def process(self, context: ProcessingContext) -> VisionAnalysisResult:
        result = self.service.inspect_image(context.file_path)
        context.artifacts["vision_analysis"] = result
        return result
