"""
NexusOCR Speech Feature Service.
Handles audio transcription and subtitle/segment generation.
"""

from __future__ import annotations

from typing import Optional

from nexusocr.engines.speech.base import BaseSpeechEngine, DefaultSpeechEngine
from nexusocr.features.speech.models import SpeechSegment, SpeechTranscriptionResult


class SpeechService:
    """Provides speech transcription capabilities."""

    def __init__(self, engine: Optional[BaseSpeechEngine] = None) -> None:
        self.engine: BaseSpeechEngine = engine or DefaultSpeechEngine()

    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> SpeechTranscriptionResult:
        """Transcribes an audio file into text and timestamped segments."""
        raw = self.engine.transcribe(audio_path, language=language)
        segments = [
            SpeechSegment(start=s.get("start", 0.0), end=s.get("end", 0.0), text=s.get("text", ""))
            for s in raw.get("segments", [])
        ]
        return SpeechTranscriptionResult(
            text=raw.get("text", ""),
            language=raw.get("language", language or "en"),
            duration_sec=raw.get("duration", 0.0),
            segments=segments,
            confidence=raw.get("confidence", 1.0),
        )
