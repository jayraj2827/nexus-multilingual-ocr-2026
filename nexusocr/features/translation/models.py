"""
NexusOCR Translation Feature Models.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class TranslationRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = None


class TranslationResult(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
