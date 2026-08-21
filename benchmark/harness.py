"""
NexusOCR Automated Benchmark Harness.
Runs the pipeline against test PDF corpora and logs CER, WER, Table F1, Latency, and Memory.
"""

from pathlib import Path
from typing import List, Dict, Any
import fitz
from benchmark.metrics import ProfileSession, ExecutionProfile, calculate_cer, calculate_wer
from pipeline import NexusOCRPipeline
import config


class BenchmarkHarness:
    """Automates multi-document OCR accuracy and resource profiling."""

    def __init__(self, use_gpu: bool = False):
        self.pipeline = NexusOCRPipeline(use_gpu=use_gpu)

    def run_single_test(self, pdf_path: str, reference_text: str = "") -> ExecutionProfile:
        """Runs the pipeline on a single PDF and returns an ExecutionProfile."""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()

        with ProfileSession(document_name=Path(pdf_path).name, total_pages=total_pages) as session:
            result = self.pipeline.process_pdf(pdf_path)

        profile = session.get_profile(
            reference_text=reference_text,
            hypothesis_text=result.full_markdown
        )
        return profile

    def create_synthetic_test_pdfs(self, output_dir: Path):
        """Generates sample test PDFs for English, Hindi, Tables, and Mixed scripts."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Monolingual English Test PDF
        doc_en = fitz.open()
        p1 = doc_en.new_page()
        p1.insert_text((50, 72), "NEXUS INVOICE STATEMENT", fontsize=18)
        p1.insert_text((50, 110), "Invoice Number: INV-2026-9042", fontsize=12)
        p1.insert_text((50, 130), "Date: 21/08/2026", fontsize=12)
        p1.insert_text((50, 150), "Total Amount: $4,580.00", fontsize=12)
        p1.insert_text((50, 180), "This document verifies high-throughput multilingual OCR extraction.", fontsize=11)
        doc_en.save(str(output_dir / "test_digital_english.pdf"))
        doc_en.close()

        # 2. Hindi / Devanagari Test PDF
        doc_hi = fitz.open()
        p2 = doc_hi.new_page()
        p2.insert_text((50, 72), "भारत सरकार - आधिकारिक प्रलेख", fontsize=16)
        p2.insert_text((50, 110), "दस्तावेज़ संख्या: 89432", fontsize=12)
        p2.insert_text((50, 130), "दिनांक: 21 अगस्त 2026", fontsize=12)
        p2.insert_text((50, 160), "यह बहुभाषी ओसीआर प्रणाली का एक परीक्षण पृष्ठ है।", fontsize=12)
        doc_hi.save(str(output_dir / "test_hindi_devanagari.pdf"))
        doc_hi.close()

        # 3. Multi-Column & Table Structure Test PDF
        doc_tbl = fitz.open()
        p3 = doc_tbl.new_page()
        p3.insert_text((50, 60), "QUARTERLY FINANCIAL SUMMARY", fontsize=16)
        # Draw a basic table
        p3.draw_rect(fitz.Rect(50, 90, 500, 200), color=(0, 0, 0), width=1)
        p3.draw_line(fitz.Point(50, 120), fitz.Point(500, 120), color=(0, 0, 0), width=1)
        p3.insert_text((60, 110), "Item Description", fontsize=11)
        p3.insert_text((250, 110), "Quantity", fontsize=11)
        p3.insert_text((400, 110), "Total ($)", fontsize=11)
        p3.insert_text((60, 145), "Enterprise OCR License", fontsize=10)
        p3.insert_text((250, 145), "5", fontsize=10)
        p3.insert_text((400, 145), "2,500.00", fontsize=10)
        p3.insert_text((60, 175), "Cloud Sync Tier", fontsize=10)
        p3.insert_text((250, 175), "1", fontsize=10)
        p3.insert_text((400, 175), "500.00", fontsize=10)
        doc_tbl.save(str(output_dir / "test_tables_financial.pdf"))
        doc_tbl.close()
