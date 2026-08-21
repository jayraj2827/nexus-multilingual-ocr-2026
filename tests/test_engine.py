"""
NexusOCR Engine Unit Tests.
Verifies Digital Extractor, Pipeline Orchestrator, and Type Contracts.
"""

from pathlib import Path
import fitz
from engine.types import DocumentResult, PageResult, ExtractionSource
from engine.digital_extractor import extract_digital_page
from pipeline import NexusOCRPipeline

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_digital_extractor():
    """Verifies Tier 1 extracts digital text and tables with high trust."""
    test_pdf = str(FIXTURES_DIR / "test_digital_english.pdf")
    assert Path(test_pdf).exists(), f"Missing test fixture {test_pdf}"

    doc = fitz.open(test_pdf)
    score, res = extract_digital_page(doc[0], 1)
    doc.close()

    assert score >= 0.85
    assert res is not None
    assert res.is_digital is True
    assert "NEXUS INVOICE STATEMENT" in res.markdown
    assert len(res.regions) > 0


def test_pipeline_orchestrator():
    """Verifies end-to-end processing returns DocumentResult schema."""
    pipeline = NexusOCRPipeline()
    test_pdf = str(FIXTURES_DIR / "test_tables_financial.pdf")
    assert Path(test_pdf).exists(), f"Missing test fixture {test_pdf}"

    result = pipeline.process_pdf(test_pdf)
    assert isinstance(result, DocumentResult)
    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert "QUARTERLY FINANCIAL SUMMARY" in result.full_markdown
    assert result.total_execution_time_ms > 0
