"""
NexusOCR Unified Pipeline Orchestrator.
Following KISS principles: explicit, transparent, and developer-friendly.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import numpy as np

from core.types import (
    PageResult, DocumentResult, ExtractedRegion, BoundingBox,
    ScriptType, TextType, EngineType
)
from core.profiler import profile_pdf_page
from core.preprocessor import rasterize_pdf_page, calculate_image_quality
from core.detector import DBNetDetector
from core.difficulty_router import DifficultyRouter
from core.recognizers.latin_v6 import LatinV6Recognizer
from core.recognizers.devanagari_v5 import DevanagariV5Recognizer
from core.recognizers.gujarati_tess import GujaratiTesseractRecognizer
from core.recognizers.handwriting import HandwritingRecognizer
from core.recognizers.vlm_fallback import VLMFallbackClient
from core.confidence import compute_multi_signal_confidence
from core.retry import execute_crop_retry
from core.layout import LayoutParser
from core.table_engine import TableEngine
from core.structure_builder import (
    sort_reading_order_rxy_cut, extract_spatial_fields, build_final_markdown
)
import config


class NexusOCRPipeline:
    """End-to-End CPU-First Adaptive Document Intelligence OCR Pipeline."""

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu

        # Initialize core components
        self.detector = DBNetDetector(use_gpu=use_gpu)
        self.router = DifficultyRouter()
        self.layout_parser = LayoutParser(use_gpu=use_gpu)
        self.table_engine = TableEngine(use_gpu=use_gpu)

        # Initialize pluggable recognizers
        self.rec_latin = LatinV6Recognizer(use_gpu=use_gpu)
        self.rec_devanagari = DevanagariV5Recognizer(use_gpu=use_gpu)
        self.rec_gujarati = GujaratiTesseractRecognizer()
        self.rec_handwriting = HandwritingRecognizer(use_gpu=use_gpu)
        self.vlm_fallback = VLMFallbackClient()

    def process_pdf(self, pdf_path: str, schema_keys: Optional[List[str]] = None) -> DocumentResult:
        """
        Processes a multi-page PDF through the adaptive pipeline.
        """
        start_time = time.perf_counter()
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        page_results: List[PageResult] = []

        total_vlm_count = 0
        trust_scores = []

        for page_idx in range(total_pages):
            page_start = time.perf_counter()
            page = doc[page_idx]
            page_num = page_idx + 1

            # --- STAGE 1: PDF Profiling & Trust Gate ---
            trust_score, native_result = profile_pdf_page(page, page_num)
            trust_scores.append(trust_score)

            if native_result is not None:
                native_result.execution_time_ms = (time.perf_counter() - page_start) * 1000.0
                page_results.append(native_result)
                continue

            # --- STAGE 2: Adaptive Rasterization ---
            page_img = rasterize_pdf_page(page, dpi=config.BASE_RASTER_DPI)
            h, w = page_img.shape[:2]
            img_quality = calculate_image_quality(page_img)

            # --- STAGE 3: Layout Ladder & Table Parsing ---
            layout_blocks = self.layout_parser.parse_layout(page_img)
            tables = []
            table_idx = 1
            for b in layout_blocks:
                if b["type"] == "table":
                    t_box = b["bbox"]
                    t_crop = page_img[int(t_box.ymin):int(t_box.ymax), int(t_box.xmin):int(t_box.xmax)]
                    table_obj = self.table_engine.extract_table(t_crop, t_box, f"page_{page_num}_table_{table_idx}")
                    if table_obj:
                        tables.append(table_obj)
                        table_idx += 1

            # --- STAGE 4: DBNet Text Detection ---
            detected_items = self.detector.detect_boxes(page_img)

            # --- STAGE 5: Script Routing & Grouped Batching ---
            batches = self.router.build_grouped_batches(detected_items)
            recognized_regions: List[ExtractedRegion] = []

            # 5a. Latin Batch (PP-OCRv6)
            if batches["latin"]:
                crops = [item[2] for item in batches["latin"]]
                results = self.rec_latin.recognize_batch(crops)
                for (orig_idx, bbox, crop, script, text_type), (txt, conf) in zip(batches["latin"], results):
                    comp_conf = compute_multi_signal_confidence(conf, txt, script, img_quality)
                    reg = ExtractedRegion(
                        id=f"p{page_num}_r{orig_idx}",
                        bbox=bbox,
                        text=txt,
                        raw_confidence=conf,
                        composite_confidence=comp_conf,
                        script=script,
                        text_type=text_type,
                        engine_used=EngineType.PPOCR_LATIN
                    )
                    # Stage 6: Multi-Signal Check & Fallback
                    reg = execute_crop_retry(reg, crop, self.rec_latin, self.vlm_fallback)
                    if reg.engine_used == EngineType.FALLBACK_B_VLM:
                        total_vlm_count += 1
                    recognized_regions.append(reg)

            # 5b. Devanagari Batch (PP-OCRv5)
            if batches["devanagari"]:
                crops = [item[2] for item in batches["devanagari"]]
                results = self.rec_devanagari.recognize_batch(crops)
                for (orig_idx, bbox, crop, script, text_type), (txt, conf) in zip(batches["devanagari"], results):
                    comp_conf = compute_multi_signal_confidence(conf, txt, script, img_quality)
                    reg = ExtractedRegion(
                        id=f"p{page_num}_r{orig_idx}",
                        bbox=bbox,
                        text=txt,
                        raw_confidence=conf,
                        composite_confidence=comp_conf,
                        script=script,
                        text_type=text_type,
                        engine_used=EngineType.PPOCR_DEVANAGARI
                    )
                    reg = execute_crop_retry(reg, crop, self.rec_devanagari, self.vlm_fallback)
                    if reg.engine_used == EngineType.FALLBACK_B_VLM:
                        total_vlm_count += 1
                    recognized_regions.append(reg)

            # 5c. Gujarati Batch (Tesseract)
            if batches["gujarati"]:
                crops = [item[2] for item in batches["gujarati"]]
                results = self.rec_gujarati.recognize_batch(crops)
                for (orig_idx, bbox, crop, script, text_type), (txt, conf) in zip(batches["gujarati"], results):
                    comp_conf = compute_multi_signal_confidence(conf, txt, script, img_quality)
                    reg = ExtractedRegion(
                        id=f"p{page_num}_r{orig_idx}",
                        bbox=bbox,
                        text=txt,
                        raw_confidence=conf,
                        composite_confidence=comp_conf,
                        script=script,
                        text_type=text_type,
                        engine_used=EngineType.TESSERACT_GUJARATI
                    )
                    reg = execute_crop_retry(reg, crop, self.rec_gujarati, self.vlm_fallback)
                    if reg.engine_used == EngineType.FALLBACK_B_VLM:
                        total_vlm_count += 1
                    recognized_regions.append(reg)

            # 5d. Handwriting Batch (PP-OCRv5 HW)
            if batches["handwriting"]:
                crops = [item[2] for item in batches["handwriting"]]
                results = self.rec_handwriting.recognize_batch(crops)
                for (orig_idx, bbox, crop, script, text_type), (txt, conf) in zip(batches["handwriting"], results):
                    comp_conf = compute_multi_signal_confidence(conf, txt, script, img_quality, is_handwritten=True)
                    reg = ExtractedRegion(
                        id=f"p{page_num}_r{orig_idx}",
                        bbox=bbox,
                        text=txt,
                        raw_confidence=conf,
                        composite_confidence=comp_conf,
                        script=script,
                        text_type=text_type,
                        engine_used=EngineType.PPOCR_HANDWRITING
                    )
                    reg = execute_crop_retry(reg, crop, self.rec_handwriting, self.vlm_fallback)
                    if reg.engine_used == EngineType.FALLBACK_B_VLM:
                        total_vlm_count += 1
                    recognized_regions.append(reg)

            # --- STAGE 7: Structure Builder & Reading Order ---
            sorted_regions = sort_reading_order_rxy_cut(recognized_regions)
            fields = extract_spatial_fields(sorted_regions, schema_keys=schema_keys)
            markdown_content = build_final_markdown(sorted_regions, tables)

            page_result = PageResult(
                page_number=page_num,
                width=w,
                height=h,
                text_layer_trust_score=trust_score,
                is_native_text=False,
                dominant_script=ScriptType.LATIN,
                regions=sorted_regions,
                tables=tables,
                reading_order_markdown=markdown_content,
                structured_fields=fields,
                execution_time_ms=(time.perf_counter() - page_start) * 1000.0,
                vlm_escalated=any(r.engine_used == EngineType.FALLBACK_B_VLM for r in sorted_regions)
            )
            page_results.append(page_result)

        doc.close()

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        total_regions = sum(len(p.regions) for p in page_results)
        vlm_rate = (total_vlm_count / total_regions) if total_regions > 0 else 0.0

        full_md = "\n\n---\n\n".join(p.reading_order_markdown for p in page_results)
        structured_json = {
            "file": Path(pdf_path).name,
            "pages": [p.dict() for p in page_results],
            "extracted_fields": {k: v for p in page_results for k, v in p.structured_fields.items()}
        }

        return DocumentResult(
            file_name=Path(pdf_path).name,
            total_pages=total_pages,
            pages=page_results,
            full_markdown=full_md,
            structured_json=structured_json,
            average_trust_score=sum(trust_scores) / len(trust_scores) if trust_scores else 0.0,
            vlm_escalation_rate=vlm_rate,
            total_execution_time_ms=total_elapsed_ms
        )
