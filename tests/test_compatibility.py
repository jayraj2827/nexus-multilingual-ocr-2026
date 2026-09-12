"""
NexusOCR Backward Compatibility Regression Tests.
Verifies that all legacy import paths, classes, functions, and variables remain 100% functional.
"""

from pathlib import Path
import pytest


def test_legacy_engine_types_imports():
    """Verifies engine.types imports and schema structure."""
    from engine.types import (
        ExtractionSource,
        BoundingBox,
        ExtractedRegion,
        TableStructure,
        PageResult,
        DocumentResult,
    )

    assert ExtractionSource.DIGITAL_NATIVE == "digital_native"
    assert ExtractionSource.DOCLING_LAYOUT == "docling_layout"
    assert ExtractionSource.OLLAMA_VLM == "ollama_vlm"

    box = BoundingBox(xmin=10.0, ymin=20.0, xmax=50.0, ymax=80.0)
    assert box.width == 40.0
    assert box.height == 60.0

    region = ExtractedRegion(id="r1", bbox=box, text="Sample Header", category="header")
    assert region.confidence == 1.0
    assert region.source == ExtractionSource.DIGITAL_NATIVE

    page = PageResult(page_number=1, width=1000, height=800, regions=[region])
    assert page.is_digital is True

    doc = DocumentResult(file_name="sample.pdf", total_pages=1, pages=[page])
    assert doc.file_name == "sample.pdf"
    assert len(doc.pages) == 1


def test_legacy_engine_init_imports():
    """Verifies engine package level exports."""
    import engine
    assert hasattr(engine, "ExtractionSource")
    assert hasattr(engine, "BoundingBox")
    assert hasattr(engine, "ExtractedRegion")
    assert hasattr(engine, "TableStructure")
    assert hasattr(engine, "PageResult")
    assert hasattr(engine, "DocumentResult")


def test_legacy_digital_extractor_imports():
    """Verifies engine.digital_extractor imports and signatures."""
    from engine.digital_extractor import extract_digital_page
    import inspect

    sig = inspect.signature(extract_digital_page)
    params = list(sig.parameters.keys())
    assert params == ["page", "page_num"]


def test_legacy_paddle_ocr_engine_imports():
    """Verifies engine.paddle_ocr_engine imports."""
    from engine.paddle_ocr_engine import PaddleOCREngine, _stub_modelscope

    engine_inst = PaddleOCREngine()
    assert hasattr(engine_inst, "process_page_image")
    assert hasattr(engine_inst, "is_available")
    assert callable(_stub_modelscope)


def test_legacy_docling_engine_imports():
    """Verifies engine.docling_engine imports."""
    from engine.docling_engine import DoclingEngine

    docling = DoclingEngine()
    assert hasattr(docling, "process_document")
    assert hasattr(docling, "is_available")


def test_legacy_pipeline_imports():
    """Verifies pipeline.py imports, classes, and logging function."""
    from pipeline import NexusOCRPipeline, log

    assert callable(log)
    p = NexusOCRPipeline()
    assert hasattr(p, "process_pdf")


def test_legacy_config_imports():
    """Verifies root config.py attributes."""
    import config

    assert hasattr(config, "BASE_DIR")
    assert hasattr(config, "DATA_DIR")
    assert hasattr(config, "UPLOAD_DIR")
    assert hasattr(config, "BASE_RASTER_DPI")
    assert hasattr(config, "TRUST_SCORE_NATIVE_THRESHOLD")
    assert hasattr(config, "SERVER_HOST")
    assert hasattr(config, "SERVER_PORT")

    assert config.BASE_RASTER_DPI == 150
    assert config.TRUST_SCORE_NATIVE_THRESHOLD == 0.85


def test_legacy_app_imports():
    """Verifies root app.py exports."""
    import app

    assert hasattr(app, "app")
    assert hasattr(app, "pipeline")
    assert hasattr(app, "BASE_DIR")
    assert hasattr(app, "frontend_dir")
    assert hasattr(app, "fixtures_dir")


def test_new_modular_package_imports():
    """Verifies new nexusocr modular hierarchy imports."""
    from nexusocr import NexusOCRPipeline, NexusOCRClient, DocumentOCRService
    from nexusocr.pipeline import PipelineRunner, PipelineStage, ProcessingContext
    from nexusocr.contracts import ExtractionSource, DocumentResult, ProcessingOptions
    from nexusocr.processors import PDFProcessor, ImageProcessor, VideoProcessor, AudioProcessor
    from nexusocr.engines import PyMuPDFEngine, PaddleOCREngine, DoclingEngine
    from nexusocr.features import DocumentOCRService, LayoutService, VisionService, SpeechService, TranslationService

    client = NexusOCRClient()
    assert hasattr(client, "process_document")
    assert hasattr(client, "inspect_image")
