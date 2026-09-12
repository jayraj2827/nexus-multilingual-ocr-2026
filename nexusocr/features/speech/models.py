"""
NexusOCR Speech Feature Models.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SpeechSegment(BaseModel):
    start: float
    end: float
    text: str


class SpeechTranscriptionResult(BaseModel):
    text: str
    language: str = "en"
    duration_sec: float = 0.0
    segments: List[SpeechSegment] = Field(default_factory=list)
    confidence: float = 1.0
