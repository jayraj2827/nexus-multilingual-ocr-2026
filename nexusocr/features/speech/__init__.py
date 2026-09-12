"""
NexusOCR Speech Feature Package.
"""

from __future__ import annotations

from nexusocr.features.speech.models import SpeechSegment, SpeechTranscriptionResult
from nexusocr.features.speech.service import SpeechService
from nexusocr.features.speech.stage import SpeechStage

__all__ = [
    "SpeechSegment",
    "SpeechTranscriptionResult",
    "SpeechService",
    "SpeechStage",
]
