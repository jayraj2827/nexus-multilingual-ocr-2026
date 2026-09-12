"""
NexusOCR Translation Feature Service.
Provides script detection and multilingual translation.
"""

from __future__ import annotations

from typing import Optional

from nexusocr.engines.translation.base import BaseTranslationEngine, DefaultTranslationEngine
from nexusocr.features.translation.models import TranslationRequest, TranslationResult


class TranslationService:
    """Provides language detection and translation capabilities."""

    def __init__(self, engine: Optional[BaseTranslationEngine] = None) -> None:
        self.engine: BaseTranslationEngine = engine or DefaultTranslationEngine()

    def detect_language(self, text: str) -> str:
        """Identifies text language script (en, hi, gu)."""
        return self.engine.detect_language(text)

    def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> TranslationResult:
        """Translates text to target language."""
        src_lang = source_language or self.detect_language(text)
        translated = self.engine.translate(text, target_lang=target_language, source_lang=src_lang)
        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_language=src_lang,
            target_language=target_language,
        )
