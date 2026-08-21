"""
NexusOCR Unified Pipeline Orchestrator — Fast 2-Tier Architecture.

Routing:
  Tier 1: PyMuPDF Digital Extraction   (<40ms   | Digital PDFs, searchable text)
  Tier 2: PaddleOCR GPU (PP-OCRv6)     (~150ms  | Scanned images, complex layouts, Indic/multilingual)
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
import numpy as np

os.environ["PYTHONUNBUFFERED"] = "1"
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.getLogger("ppocr").setLevel(logging.WARNING)

from engine.types import PageResult, DocumentResult, ExtractionSource
from engine.digital_extractor import extract_digital_page
from engine.paddle_ocr_engine import PaddleOCREngine
import config


def log(msg: str):
    print(msg, flush=True)


class NexusOCRPipeline:
    """End-to-End Document Intelligence Pipeline."""

    def __init__(self):
        log("[NexusOCR] Initializing NexusOCR Pipeline...")
        self.paddle_engine = PaddleOCREngine()
        log("[NexusOCR] Pipeline ready.")

    def process_pdf(self, pdf_path: str, max_pages: Optional[int] = None) -> DocumentResult:
        """
        Routes each page through the fastest available engine:
          1. PyMuPDF   → trust score >= 0.85 (digital text layer present, <40ms)
          2. PaddleOCR → RTX 4060 CUDA GPU for scanned pages (~150ms)
        """
        file_name = Path(pdf_path).name
        start_time = time.perf_counter()
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
        page_results: List[PageResult] = []
        trust_scores: List[float] = []

        log(f"\n[NexusOCR] [Document] '{file_name}' | Total Pages: {total_pages} (Processing: {pages_to_process})")

        for page_idx in range(pages_to_process):
            page_start = time.perf_counter()
            page = doc[page_idx]
            page_num = page_idx + 1
            log(f"[NexusOCR] -> Page {page_num}/{pages_to_process}...")

            try:
                # ── TIER 1: PyMuPDF Fast Digital Extraction ──────────────────
                trust_score, digital_result = extract_digital_page(page, page_num)
                trust_scores.append(trust_score)

                if digital_result is not None:
                    page_results.append(digital_result)
                    log(f"[NexusOCR]    [Tier 1: Digital PyMuPDF] Score={trust_score:.2f} | {digital_result.execution_time_ms:.1f}ms [OK]")
                    continue

                log(f"[NexusOCR]    [Tier 1: Score={trust_score:.2f} < 0.85] -> Routing to PaddleOCR GPU")

                # ── TIER 2: PaddleOCR on RTX 4060 GPU ────────────────────────
                pix = page.get_pixmap(dpi=config.BASE_RASTER_DPI)
                img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                if pix.n == 4:
                    img_np = img_np[:, :, :3]

                paddle_result = self.paddle_engine.process_page_image(img_np, page_num)
                if paddle_result:
                    page_results.append(paddle_result)
                    log(f"[NexusOCR]    [Tier 2: PaddleOCR GPU] Page {page_num} done in {paddle_result.execution_time_ms:.1f}ms [OK]")
                    continue

                # ── Fallback if no text extracted ─────────────────────────────
                elapsed_fallback = (time.perf_counter() - page_start) * 1000.0
                page_results.append(PageResult(
                    page_number=page_num,
                    width=pix.width,
                    height=pix.height,
                    is_digital=False,
                    trust_score=trust_score,
                    markdown=f"*(Page {page_num}: no extractable content)*",
                    source=ExtractionSource.DIGITAL_NATIVE,
                    execution_time_ms=elapsed_fallback
                ))

            except Exception as page_err:
                elapsed_err = (time.perf_counter() - page_start) * 1000.0
                log(f"[NexusOCR] [Warning] Page {page_num} error: {page_err}")
                page_results.append(PageResult(
                    page_number=page_num,
                    width=600, height=800,
                    is_digital=False,
                    trust_score=0.0,
                    markdown=f"*(Page {page_num} error: {page_err})*",
                    source=ExtractionSource.DIGITAL_NATIVE,
                    execution_time_ms=elapsed_err
                ))

        doc.close()
        total_ms = (time.perf_counter() - start_time) * 1000.0
        full_md = "\n\n---\n\n".join(p.markdown for p in page_results)

        log(f"[NexusOCR] [Complete] '{file_name}' — {len(page_results)} pages in {total_ms:.1f}ms\n")

        return DocumentResult(
            file_name=file_name,
            total_pages=total_pages,
            pages=page_results,
            full_markdown=full_md,
            structured_json={"file": file_name, "total_pages": total_pages, "pages": [p.model_dump() for p in page_results]},
            average_trust_score=sum(trust_scores) / len(trust_scores) if trust_scores else 1.0,
            total_execution_time_ms=total_ms
        )
