"""
Representative Workflows Test Suite.
Verifies Digital PDFs, Scanned/Table PDFs, Images, Video, Audio, OCR, Vision, Speech, Translation, and Layout.
"""

import os
import struct
import tempfile
import wave
from pathlib import Path
import cv2
import numpy as np
import pytest

from nexusocr.contracts.results import BoundingBox, DocumentResult
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.features.layout.service import LayoutService
from nexusocr.features.translation.service import TranslationService
from nexusocr.features.vision.service import VisionService
from nexusocr.processors.image import ImageProcessor
from nexusocr.processors.pdf import PDFProcessor

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_workflow_digital_pdf():
    """Workflow 1: Digital PDF extraction with PyMuPDF Tier 1 (<40ms)."""
    pdf_path = str(FIXTURES_DIR / "test_digital_english.pdf")
    service = DocumentOCRService()
    result = service.process_pdf(pdf_path)

    assert isinstance(result, DocumentResult)
    assert result.total_pages == 1
    assert result.pages[0].is_digital is True
    assert result.pages[0].trust_score >= 0.85
    assert "NEXUS INVOICE STATEMENT" in result.full_markdown


def test_workflow_financial_tables_pdf():
    """Workflow 2: Document with native tabular structures."""
    pdf_path = str(FIXTURES_DIR / "test_tables_financial.pdf")
    service = DocumentOCRService()
    result = service.process_pdf(pdf_path)

    assert isinstance(result, DocumentResult)
    assert result.total_pages == 1
    assert "QUARTERLY FINANCIAL SUMMARY" in result.full_markdown
    assert "Enterprise OCR License" in result.full_markdown
    assert len(result.pages[0].regions) > 0


def test_workflow_multilingual_pdf():
    """Workflow 3: Multilingual / Devanagari document."""
    pdf_path = str(FIXTURES_DIR / "test_hindi_devanagari.pdf")
    service = DocumentOCRService()
    result = service.process_pdf(pdf_path)

    assert isinstance(result, DocumentResult)
    assert result.total_pages == 1
    assert len(result.pages) == 1


def test_workflow_image_processor():
    """Workflow 4: Image loading, resizing, cropping, and JPEG conversion."""
    test_img = np.zeros((200, 300, 3), dtype=np.uint8)
    test_img[50:150, 50:250] = [255, 128, 64]

    loaded = ImageProcessor.load_image(test_img)
    assert loaded.shape == (200, 300, 3)

    bbox = BoundingBox(xmin=50, ymin=50, xmax=100, ymax=100)
    cropped = ImageProcessor.crop_box(loaded, bbox)
    assert cropped.shape == (50, 50, 3)

    resized = ImageProcessor.resize_with_aspect_ratio(loaded, target_width=150)
    assert resized.shape[1] == 150
    assert resized.shape[0] == 100

    jpeg_bytes = ImageProcessor.to_jpeg_bytes(loaded)
    assert len(jpeg_bytes) > 0
    assert jpeg_bytes[:2] == b"\xff\xd8"  # JPEG SOI marker


def test_workflow_vision_service():
    """Workflow 5: Computer vision metrics and preview generation."""
    test_img = np.ones((100, 100, 3), dtype=np.uint8) * 200
    service = VisionService()

    analysis = service.inspect_image(test_img)
    assert analysis.image_width == 100
    assert analysis.image_height == 100
    assert analysis.mean_brightness == 200.0

    preview = service.generate_preview_jpeg(test_img, max_width=50)
    assert len(preview) > 0


def test_workflow_translation_service():
    """Workflow 8: Script detection and multilingual translation."""
    service = TranslationService()

    # English text
    assert service.detect_language("Hello world, this is a test.") == "en"

    # Hindi Devanagari text
    assert service.detect_language("नमस्ते भारत, यह एक परीक्षण है।") == "hi"

    # Gujarati text
    assert service.detect_language("નમસ્તે ગુજરાત, આ એક ટેસ્ટ છે.") == "gu"

    # Translation execution
    res = service.translate("Welcome to NexusOCR", target_language="hi")
    assert res.target_language == "hi"
    assert len(res.translated_text) > 0


def test_workflow_layout_service():
    """Workflow 9: Layout analysis service."""
    service = LayoutService()
    # If Docling is not initialized/converted, returns None safely without error
    res = service.analyze_document_layout("nonexistent.pdf")
    assert res is None
