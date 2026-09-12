"""
Pillar 2: IBM Docling Layout & TableFormer Engine (Compatibility Bridge).
Re-exports DoclingEngine from nexusocr.engines.ocr.docling.
"""

from __future__ import annotations

from nexusocr.engines.ocr.docling import DoclingEngine

__all__ = ["DoclingEngine"]
