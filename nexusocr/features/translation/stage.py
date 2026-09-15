"""
NexusOCR Translation Pipeline Stage.
"""

from __future__ import annotations

from typing import Optional

from nexusocr.features.translation.models import TranslationResult
from nexusocr.features.translation.service import TranslationService
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.stage import PipelineStage


class TranslationStage(PipelineStage):
    """Pipeline stage translating document markdown if requested in options."""

    def __init__(
        self,
        service: Optional[TranslationService] = None,
        name: str = "TranslationStage",
        enabled: bool = True
    ) -> None:
        super().__init__(name=name, enabled=enabled)
        self.service: TranslationService = service or TranslationService()

    def can_handle(self, context: ProcessingContext) -> bool:
        return (
            super().can_handle(context)
            and context.options.enable_translation
            and bool(context.options.target_language)
            and context.document_result is not None
        )

    def process(self, context: ProcessingContext) -> Optional[TranslationResult]:
        if context.document_result is None or not context.options.target_language:
            return None

        result = self.service.translate(
            text=context.document_result.full_markdown,
            target_language=context.options.target_language
        )
        context.artifacts["translated_markdown"] = result.translated_text
        return result
