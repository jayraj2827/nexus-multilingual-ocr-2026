"""
NexusOCR Processors Package.
Reusable technical operations for PDF, image, Office documents, and markup files.
"""

from __future__ import annotations

from nexusocr.processors.pdf import PDFProcessor
from nexusocr.processors.image import ImageProcessor
from nexusocr.processors.office import (
    DocxProcessor,
    SpreadsheetProcessor,
    PresentationProcessor,
)
from nexusocr.processors.text_markup import TextMarkupProcessor

__all__ = [
    "PDFProcessor",
    "ImageProcessor",
    "DocxProcessor",
    "SpreadsheetProcessor",
    "PresentationProcessor",
    "TextMarkupProcessor",
]
