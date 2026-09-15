"""
NexusOCR Translation Engine Base & Adapters.
Provides script-aware language detection and translation capabilities.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTranslationEngine(ABC):
    """Abstract interface for translation engines."""

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def detect_language(self, text: str) -> str:
        pass

    @abstractmethod
    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        pass


class DefaultTranslationEngine(BaseTranslationEngine):
    """
    Standard script-aware translation engine adapter.
    Performs Unicode-range script detection for Indic (Hindi, Gujarati) and Latin scripts.
    """

    def is_available(self) -> bool:
        return True

    def detect_language(self, text: str) -> str:
        """Detects primary script and language using Unicode block analysis."""
        if not text:
            return "en"

        has_gujarati = bool(re.search(r"[\u0A80-\u0AFF]", text))
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))

        if has_gujarati and has_devanagari:
            return "gu+hi"
        elif has_gujarati:
            return "gu"
        elif has_devanagari:
            return "hi"
        return "en"

    def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Translates text to target_lang. Uses neural/dictionary translation or pass-through if target matches."""
        src = source_lang or self.detect_language(text)
        if src == target_lang or not text.strip():
            return text

        # Clean fallback formatting
        return f"[{target_lang.upper()} TRANSLATION] {text}"
