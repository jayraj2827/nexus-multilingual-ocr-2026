"""
NexusOCR Speech Pipeline Stage.
"""

from __future__ import annotations

from typing import Optional

from nexusocr.features.speech.models import SpeechTranscriptionResult
from nexusocr.features.speech.service import SpeechService
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.stage import PipelineStage


class SpeechStage(PipelineStage):
    """Pipeline stage executing speech-to-text transcription."""

    def __init__(
        self,
        service: Optional[SpeechService] = None,
        name: str = "SpeechStage",
        enabled: bool = True
    ) -> None:
        super().__init__(name=name, enabled=enabled)
        self.service: SpeechService = service or SpeechService()

    def can_handle(self, context: ProcessingContext) -> bool:
        ext = context.file_path.lower()
        is_audio = ext.endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg"))
        return super().can_handle(context) and is_audio

    def process(self, context: ProcessingContext) -> SpeechTranscriptionResult:
        result = self.service.transcribe_audio(
            audio_path=context.file_path,
            language=context.options.target_language
        )
        context.artifacts["speech_transcription"] = result
        return result
