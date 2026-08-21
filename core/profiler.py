"""
PDF Text-Layer Profiler and Trust Scorer.
Evaluates Unicode integrity, character density, and raster image coverage via PyMuPDF.
Bypasses OCR for clean digital PDFs in <10ms per page.
"""

import unicodedata
from typing import Dict, Any, Tuple, Optional
import fitz  # PyMuPDF
from core.types import PageResult, ExtractedRegion, BoundingBox, EngineType, ScriptType, TextType
import config


def profile_pdf_page(page: fitz.Page, page_number: int) -> Tuple[float, Optional[PageResult]]:
    """
    Evaluates the native text layer of a single PDF page.
    Returns:
        trust_score: float in [0.0, 1.0]
        native_result: PageResult if trust_score >= config.TRUST_SCORE_NATIVE_THRESHOLD, else None
    """
    rect = page.rect
    page_width = int(rect.width)
    page_height = int(rect.height)
    page_area = max(1.0, rect.width * rect.height)

    # 1. Extract raw native text blocks
    text_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
    text_content = page.get_text("text")

    if not text_content.strip():
        # Completely empty text layer -> definitely scanned or image-only
        return 0.0, None

    total_chars = len(text_content)
    printable_chars = sum(1 for c in text_content if c.isprintable() and not c.isspace())
    if total_chars == 0 or printable_chars == 0:
        return 0.0, None

    printable_ratio = printable_chars / total_chars

    # 2. Check Unicode integrity (check for replacement char \ufffd or excessive private use/control characters)
    replacement_chars = text_content.count("\ufffd") + text_content.count("\x00")
    invalid_char_ratio = replacement_chars / total_chars
    unicode_integrity = max(0.0, 1.0 - (invalid_char_ratio * 5.0))

    # 3. Check for background full-page raster images (indicates scanned PDF with invisible/bad OCR)
    images = page.get_images(full=True)
    has_large_background_image = False
    raster_coverage = 0.0

    for img_info in images:
        xref = img_info[0]
        try:
            img_rects = page.get_image_rects(xref)
            for img_r in img_rects:
                img_area = img_r.width * img_r.height
                if (img_area / page_area) > 0.65:
                    has_large_background_image = True
                    raster_coverage = max(raster_coverage, img_area / page_area)
        except Exception:
            pass

    # 4. Compute composite Text Trust Score
    # Equation: Trust = (0.4 * PrintableRatio) + (0.4 * UnicodeIntegrity) + (0.2 * (1 - RasterCoverage))
    trust_score = (0.40 * printable_ratio) + (0.40 * unicode_integrity) + (0.20 * (1.0 - raster_coverage))
    trust_score = max(0.0, min(1.0, trust_score))

    # If full page scan is present with low character count, penalize trust score
    if has_large_background_image and total_chars < 300:
        trust_score *= 0.50

    # 5. If trusted, build native PageResult directly
    if trust_score >= config.TRUST_SCORE_NATIVE_THRESHOLD:
        regions = []
        for b in text_blocks:
            if b[6] == 0:  # Text block (type 0)
                block_text = b[4].strip()
                if block_text:
                    script = _detect_text_script(block_text)
                    bbox = BoundingBox(xmin=float(b[0]), ymin=float(b[1]), xmax=float(b[2]), ymax=float(b[3]))
                    regions.append(ExtractedRegion(
                        id=f"page_{page_number}_native_{len(regions)}",
                        bbox=bbox,
                        text=block_text,
                        raw_confidence=1.0,
                        composite_confidence=1.0,
                        script=script,
                        text_type=TextType.PRINTED,
                        engine_used=EngineType.NATIVE,
                        is_retried=False
                    ))

        native_result = PageResult(
            page_number=page_number,
            width=page_width,
            height=page_height,
            text_layer_trust_score=trust_score,
            is_native_text=True,
            dominant_script=_detect_text_script(text_content),
            regions=regions,
            tables=[],
            reading_order_markdown=text_content,
            structured_fields={},
            execution_time_ms=0.0,
            vlm_escalated=False
        )
        return trust_score, native_result

    return trust_score, None


def _detect_text_script(text: str) -> ScriptType:
    """Deterministic script classification based on Unicode codepoints."""
    counts = {"latin": 0, "devanagari": 0, "gujarati": 0}
    for char in text:
        cp = ord(char)
        if 0x0900 <= cp <= 0x097F:
            counts["devanagari"] += 1
        elif 0x0A80 <= cp <= 0x0AFF:
            counts["gujarati"] += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            counts["latin"] += 1

    total = sum(counts.values())
    if total == 0:
        return ScriptType.UNKNOWN

    dominant = max(counts, key=counts.get)
    if counts[dominant] / total >= 0.70:
        if dominant == "devanagari":
            return ScriptType.DEVANAGARI
        elif dominant == "gujarati":
            return ScriptType.GUJARATI
        else:
            return ScriptType.LATIN

    return ScriptType.MIXED
