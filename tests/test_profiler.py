"""
Unit tests for PDF Profiler & Text Trust Scorer.
"""

import fitz
import pytest
from core.profiler import profile_pdf_page, _detect_text_script
from core.types import ScriptType


def test_detect_text_script():
    # English / Latin
    assert _detect_text_script("This is standard English text.") == ScriptType.LATIN

    # Hindi / Devanagari
    assert _detect_text_script("यह हिंदी में लिखा गया एक परीक्षण वाक्य है।") == ScriptType.DEVANAGARI

    # Gujarati
    assert _detect_text_script("આ ગુજરાતી ભાષામાં લખાયેલ વાક્ય છે.") == ScriptType.GUJARATI


def test_profile_digital_pdf_trust_score(tmp_path):
    # Create a synthetic clean digital PDF
    pdf_file = tmp_path / "digital_test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Standard Digital Document with clean text layer.")
    doc.save(str(pdf_file))
    doc.close()

    # Test profiler
    doc = fitz.open(str(pdf_file))
    trust_score, native_result = profile_pdf_page(doc[0], 1)
    doc.close()

    assert trust_score >= 0.85
    assert native_result is not None
    assert native_result.is_native_text is True
    assert len(native_result.regions) > 0
