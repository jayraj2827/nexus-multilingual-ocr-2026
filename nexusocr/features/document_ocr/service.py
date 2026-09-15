"""
NexusOCR Document & Image Intelligence Service.
Coordinates multi-format document processing: PDF, multi-page TIFF, raster images, Office documents, and markup.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz
import numpy as np

import nexusocr.config as config
from nexusocr.contracts.formats import FormatCategory, FormatResolver
from nexusocr.contracts.input import ProcessingOptions
from nexusocr.contracts.results import (
    BoundingBox,
    DocumentResult,
    ExtractedRegion,
    ExtractionSource,
    PageResult,
    TableStructure,
)
from nexusocr.engines.ocr.paddleocr import PaddleOCREngine
from nexusocr.engines.ocr.pymupdf import extract_digital_page
from nexusocr.features.document_ocr.forms import FormDataExtractor
from nexusocr.logging import log
from nexusocr.processors.image import ImageProcessor
from nexusocr.processors.office import (
    DocxProcessor,
    PresentationProcessor,
    SpreadsheetProcessor,
)
from nexusocr.processors.text_markup import TextMarkupProcessor


def _sanitize_for_json(val: Any) -> Any:
    """Recursively removes raw bytes to prevent UTF-8 decode errors during JSON serialization."""
    if isinstance(val, (bytes, bytearray)):
        return f"<{len(val)} bytes>"
    if isinstance(val, dict):
        return {k: _sanitize_for_json(v) for k, v in val.items() if k != "embedded_images"}
    if isinstance(val, list):
        return [_sanitize_for_json(v) for v in val]
    return val


class DocumentOCRService:
    """
    End-to-End Document Intelligence Service.
    Supports PDF (2-Tier routing), raster/multi-page images (OCR), Office (DOCX, XLSX, PPTX), and text/markup.
    """

    def __init__(self, paddle_engine: Optional[PaddleOCREngine] = None) -> None:
        self.paddle_engine = paddle_engine or PaddleOCREngine()

    def process_document(
        self,
        file_path: str,
        options: Optional[ProcessingOptions] = None
    ) -> DocumentResult:
        """
        Universal entry point to process any supported document or image format.
        Validates file type and routes through capability-based extraction.
        Rejects audio and video media explicitly.
        """
        cap = FormatResolver.validate_file(file_path)
        opts = options or ProcessingOptions()

        if cap.category == FormatCategory.PDF:
            return self.process_pdf(file_path, max_pages=opts.max_pages)
        elif cap.category == FormatCategory.IMAGE:
            return self._process_image_file(file_path, opts)
        elif cap.category == FormatCategory.DOCX:
            return self._process_docx_file(file_path, opts)
        elif cap.category == FormatCategory.SPREADSHEET:
            return self._process_spreadsheet_file(file_path, opts)
        elif cap.category == FormatCategory.PRESENTATION:
            return self._process_presentation_file(file_path, opts)
        elif cap.category == FormatCategory.TEXT_MARKUP:
            return self._process_text_markup_file(file_path, opts)
        elif cap.category == FormatCategory.EPUB:
            return self._process_epub_file(file_path, opts)

        # Fallback to PDF processing
        return self.process_pdf(file_path, max_pages=opts.max_pages)

    def process_pdf(self, pdf_path: str, max_pages: Optional[int] = None) -> DocumentResult:
        """
        Routes each PDF page through the fastest available engine:
          1. PyMuPDF   → trust score >= 0.85 (digital text layer present, <40ms)
          2. PaddleOCR → Visual OCR for scanned pages and embedded images
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
                    # ── Scan for embedded images/diagrams/figures in digital PDF page ──
                    try:
                        emb_images = page.get_images(full=True)
                        emb_cards = []
                        seen_xrefs = set()
                        for img_idx, img_info in enumerate(emb_images):
                            xref = img_info[0]
                            if xref in seen_xrefs:
                                continue
                            seen_xrefs.add(xref)

                            img_np = None
                            iw, ih = 0, 0

                            # Safe native extraction via PyMuPDF Pixmap
                            try:
                                pix = fitz.Pixmap(doc, xref)
                                if pix.n != 3 or pix.colorspace != fitz.csRGB:
                                    pix = fitz.Pixmap(fitz.csRGB, pix)
                                iw, ih = pix.width, pix.height
                                if iw < 40 or ih < 40:
                                    continue
                                img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((ih, iw, 3))
                            except Exception:
                                # Fallback via extract_image and ImageProcessor
                                try:
                                    base_img = doc.extract_image(xref)
                                    if base_img and "image" in base_img:
                                        iw = base_img.get("width", 0)
                                        ih = base_img.get("height", 0)
                                        if iw < 40 or ih < 40:
                                            continue
                                        img_np = ImageProcessor.load_image(base_img["image"])
                                        ih, iw = img_np.shape[:2]
                                except Exception as fallback_err:
                                    log(f"[NexusOCR] [Warning] Failed extracting image xref {xref} on Page {page_num}: {fallback_err}")
                                    continue

                            if img_np is None or img_np.size == 0:
                                continue

                            try:
                                desc = ImageProcessor.describe_image(img_np)
                                caption = desc.get("caption", f"Embedded Image #{len(emb_cards)+1}")
                                color_str = "Monochrome / Grayscale" if desc.get("is_monochrome") else "Full Color"

                                # Placement rect on page
                                rects = page.get_image_rects(xref)
                                rect_str = ""
                                bbox = None
                                if rects:
                                    r = rects[0]
                                    sx = digital_result.width / page.rect.width if page.rect.width > 0 else 1.0
                                    sy = digital_result.height / page.rect.height if page.rect.height > 0 else 1.0
                                    bbox = BoundingBox(
                                        xmin=r.x0 * sx,
                                        ymin=r.y0 * sy,
                                        xmax=r.x1 * sx,
                                        ymax=r.y1 * sy
                                    )
                                    rect_str = f" `[{int(bbox.xmin)}, {int(bbox.ymin)}, {int(bbox.xmax)}, {int(bbox.ymax)}]`"
                                    digital_result.regions.append(ExtractedRegion(
                                        id=f"p{page_num}_fig_{len(emb_cards)+1}",
                                        bbox=bbox,
                                        text=f"[Embedded Image #{len(emb_cards)+1}: {caption}]",
                                        category="figure",
                                        confidence=0.95,
                                        source=ExtractionSource.DOCLING_LAYOUT
                                    ))

                                # OCR text inside embedded image
                                emb_ocr_res = self.paddle_engine.process_page_image(img_np, page_num=len(emb_cards)+1)
                                ocr_text = ""
                                if emb_ocr_res and emb_ocr_res.markdown and not emb_ocr_res.markdown.startswith("*("):
                                    ocr_text = emb_ocr_res.markdown

                                    # Map text regions to page coordinates if placement rect exists
                                    if bbox and emb_ocr_res.regions:
                                        bw_scale = (bbox.xmax - bbox.xmin) / max(1.0, float(iw))
                                        bh_scale = (bbox.ymax - bbox.ymin) / max(1.0, float(ih))
                                        for t_idx, t_reg in enumerate(emb_ocr_res.regions):
                                            sub_b = t_reg.bbox
                                            mapped_b = BoundingBox(
                                                xmin=bbox.xmin + sub_b.xmin * bw_scale,
                                                ymin=bbox.ymin + sub_b.ymin * bh_scale,
                                                xmax=bbox.xmin + sub_b.xmax * bw_scale,
                                                ymax=bbox.ymin + sub_b.ymax * bh_scale,
                                            )
                                            digital_result.regions.append(ExtractedRegion(
                                                id=f"p{page_num}_fig{len(emb_cards)+1}_t{t_idx+1}",
                                                bbox=mapped_b,
                                                text=t_reg.text,
                                                category="text",
                                                confidence=t_reg.confidence,
                                                source=ExtractionSource.PADDLE_OCR
                                            ))

                                card_lines = [
                                    f"### Embedded Image #{len(emb_cards)+1}{rect_str}",
                                    f"> **Visual Caption**: {caption}",
                                    f"> - **Dimensions**: {iw}x{ih} px",
                                    f"> - **Color Profile**: {color_str}"
                                ]
                                if ocr_text:
                                    card_lines.append(">\n> **Extracted Text from Image**:\n" + "\n".join(f"> {line}" for line in ocr_text.splitlines()))

                                emb_cards.append("\n".join(card_lines))
                            except Exception as card_err:
                                log(f"[NexusOCR] [Warning] Error processing embedded image xref {xref} on Page {page_num}: {card_err}")

                        if emb_cards:
                            digital_result.markdown += "\n\n" + "\n\n".join(emb_cards)
                    except Exception as emb_err:
                        log(f"[NexusOCR] [Warning] Embedded image inspection error on Page {page_num}: {emb_err}")

                    page_results.append(digital_result)
                    log(f"[NexusOCR]    [Tier 1: Digital PyMuPDF] Score={trust_score:.2f} | {digital_result.execution_time_ms:.1f}ms [OK]")
                    continue

                log(f"[NexusOCR]    [Tier 1: Score={trust_score:.2f} < 0.85] -> Routing to PaddleOCR")

                # ── TIER 2: PaddleOCR on GPU or CPU ──────────────────────────
                pix = page.get_pixmap(dpi=config.BASE_RASTER_DPI)
                img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                if pix.n == 4:
                    img_np = img_np[:, :, :3]

                paddle_result = self.paddle_engine.process_page_image(img_np, page_num)
                if paddle_result and paddle_result.markdown and not paddle_result.markdown.startswith("*("):
                    page_results.append(paddle_result)
                    log(f"[NexusOCR]    [Tier 2: PaddleOCR] Page {page_num} done in {paddle_result.execution_time_ms:.1f}ms [OK]")
                    continue

                # ── Fallback if no text extracted ─────────────────────────────
                elapsed_fallback = (time.perf_counter() - page_start) * 1000.0
                fallback_regions = [
                    ExtractedRegion(
                        id=f"p{page_num}_r{b_i+1}",
                        bbox=b,
                        text=f"[Visual Region #{b_i+1}]",
                        category="text",
                        confidence=0.85,
                        source=ExtractionSource.DOCLING_LAYOUT
                    )
                    for b_i, b in enumerate(detected_bboxes)
                ]
                fb_md = f"*(Page {page_num}: no text detected)*"
                page_results.append(PageResult(
                    page_number=page_num,
                    width=pix.width,
                    height=pix.height,
                    is_digital=False,
                    trust_score=trust_score,
                    regions=fallback_regions,
                    markdown=fb_md,
                    source=ExtractionSource.DOCLING_LAYOUT,
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

        # Extract structured form fields & key-value entities
        form_data = FormDataExtractor.extract_form_data(full_md)

        log(f"[NexusOCR] [Complete] '{file_name}' — {len(page_results)} pages in {total_ms:.1f}ms\n")

        return DocumentResult(
            file_name=file_name,
            total_pages=total_pages,
            format="PDF",
            pages=page_results,
            full_markdown=full_md,
            structured_json={
                "file": file_name,
                "total_pages": total_pages,
                "format": "PDF",
                "form_data": form_data,
                "pages": [p.model_dump() for p in page_results]
            },
            average_trust_score=sum(trust_scores) / len(trust_scores) if trust_scores else 1.0,
            total_execution_time_ms=total_ms
        )

    # ── Non-PDF Format Handlers ────────────────────────────────────────────────

    def _process_image_file(self, file_path: str, options: ProcessingOptions) -> DocumentResult:
        """Processes single or multi-page images (PNG, JPG, TIFF, BMP, WebP) via OCR."""
        file_name = Path(file_path).name
        start_time = time.perf_counter()
        frames = ImageProcessor.load_multi_page_image(file_path)
        total_frames = len(frames)
        limit = min(total_frames, options.max_pages) if options.max_pages else total_frames

        log(f"\n[NexusOCR] [Image] '{file_name}' | Total Frames/Pages: {total_frames} (Processing: {limit})")

        page_results: List[PageResult] = []
        for idx in range(limit):
            page_start = time.perf_counter()
            page_num = idx + 1
            frame = frames[idx]
            h, w = frame.shape[:2]

            # Generate visual description & caption metadata
            visual_desc = ImageProcessor.describe_image(frame)
            caption_text = visual_desc.get("caption", f"Image Frame {page_num}")
            detected_bboxes = visual_desc.get("text_regions", [])

            # Attempt neural OCR
            paddle_res = self.paddle_engine.process_page_image(frame, page_num)
            
            frame_title = f"# Image Analysis: {file_name}" if total_frames == 1 else f"# Frame {page_num}: {file_name}"
            color_str = 'Monochrome / Grayscale' if visual_desc.get('is_monochrome') else 'Full Color'

            if paddle_res and paddle_res.markdown and not paddle_res.markdown.startswith("*("):
                # Neural OCR succeeded with text
                ocr_body = paddle_res.markdown
                md_parts = [
                    frame_title,
                    "",
                    "## Visual Summary & Caption",
                    f"> **Caption**: {caption_text}",
                    f"> - **Dimensions**: {w}x{h} px",
                    f"> - **Color Profile**: {color_str}",
                    f"> - **Detected Text Lines**: {len(paddle_res.regions)}",
                    "",
                    "## Transcribed Content",
                    ocr_body
                ]
                paddle_res.markdown = "\n".join(md_parts)
                page_results.append(paddle_res)
            else:
                # Convert detected visual text regions into ExtractedRegion objects
                regions: List[ExtractedRegion] = []
                for r_idx, box in enumerate(detected_bboxes):
                    regions.append(ExtractedRegion(
                        id=f"img_p{page_num}_r{r_idx+1}",
                        bbox=box,
                        text=f"[Visual Text Region #{r_idx+1}]",
                        category="text",
                        confidence=0.85,
                        source=ExtractionSource.DOCLING_LAYOUT
                    ))

                elapsed = (time.perf_counter() - page_start) * 1000.0
                
                md_parts = [
                    frame_title,
                    "",
                    "## Visual Summary & Caption",
                    f"> **Caption**: {caption_text}",
                    f"> - **Dimensions**: {w}x{h} px",
                    f"> - **Color Profile**: {color_str}",
                    f"> - **Visual Text Regions**: {len(detected_bboxes)} detected",
                ]
                if detected_bboxes:
                    md_parts.append("\n### Detected Layout Regions")
                    for b_i, b in enumerate(detected_bboxes):
                        md_parts.append(f"- **Region {b_i+1}**: `[{int(b.xmin)}, {int(b.ymin)}, {int(b.xmax)}, {int(b.ymax)}]`")
                else:
                    md_parts.append("\n*(No text detected in this image)*")

                page_results.append(PageResult(
                    page_number=page_num,
                    width=w,
                    height=h,
                    is_digital=False,
                    trust_score=0.90,
                    regions=regions,
                    markdown="\n".join(md_parts),
                    source=ExtractionSource.DOCLING_LAYOUT,
                    execution_time_ms=elapsed,
                ))

        total_ms = (time.perf_counter() - start_time) * 1000.0
        full_md = "\n\n---\n\n".join(p.markdown for p in page_results)
        form_data = FormDataExtractor.extract_form_data(full_md)

        # If key-value entities or forms are detected in the image, append structured table section
        if form_data.get("key_value_pairs"):
            kv_lines = ["\n\n## Extracted Key-Value Entities\n", "| Field | Extracted Value |", "| :--- | :--- |"]
            for k, v in form_data["key_value_pairs"].items():
                kv_lines.append(f"| **{k}** | {v} |")
            full_md += "\n".join(kv_lines)

        log(f"[NexusOCR] [Image Complete] '{file_name}' — {len(page_results)} frame(s) in {total_ms:.1f}ms\n")

        return DocumentResult(
            file_name=file_name,
            total_pages=total_frames,
            format="IMAGE",
            pages=page_results,
            full_markdown=full_md,
            structured_json={
                "file": file_name,
                "total_pages": total_frames,
                "format": "IMAGE",
                "form_data": form_data,
                "pages": [p.model_dump() for p in page_results]
            },
            average_trust_score=0.95,
            total_execution_time_ms=total_ms,
        )

    def _process_docx_file(self, file_path: str, options: ProcessingOptions) -> DocumentResult:
        """Processes Word .docx files with native structure extraction and embedded image OCR."""
        file_name = Path(file_path).name
        start_time = time.perf_counter()
        data = DocxProcessor.extract_document(file_path)

        page_regions: List[ExtractedRegion] = []
        embedded_cards: List[str] = []

        if options.enable_ocr and data.get("embedded_images"):
            for img_idx, img_bytes in enumerate(data["embedded_images"]):
                try:
                    img_np = ImageProcessor.load_image(img_bytes)
                    ih, iw = img_np.shape[:2]
                    if iw < 40 or ih < 40:
                        continue
                    desc = ImageProcessor.describe_image(img_np)
                    caption = desc.get("caption", f"Embedded Image #{img_idx+1}")
                    color_str = "Monochrome / Grayscale" if desc.get("is_monochrome") else "Full Color"

                    emb_ocr = self.paddle_engine.process_page_image(img_np, page_num=img_idx + 1)
                    ocr_text = emb_ocr.markdown if (emb_ocr and emb_ocr.markdown and not emb_ocr.markdown.startswith("*(")) else ""

                    card_lines = [
                        f"### Embedded Image #{img_idx+1}",
                        f"> **Visual Caption**: {caption}",
                        f"> - **Dimensions**: {iw}x{ih} px",
                        f"> - **Color Profile**: {color_str}",
                    ]
                    if ocr_text:
                        card_lines.append(">\n> **Extracted Text from Image**:\n" + "\n".join(f"> {line}" for line in ocr_text.splitlines()))

                    embedded_cards.append("\n".join(card_lines))

                    page_regions.append(ExtractedRegion(
                        id=f"docx_fig_{img_idx+1}",
                        bbox=BoundingBox(xmin=50, ymin=50 + img_idx * 150, xmax=min(750, 50 + iw), ymax=min(1050, 50 + img_idx * 150 + ih)),
                        text=f"[Embedded Image #{img_idx+1}: {caption}]",
                        category="figure",
                        confidence=0.95,
                        source=ExtractionSource.DOCLING_LAYOUT
                    ))

                    if emb_ocr and emb_ocr.regions:
                        for t_idx, t_reg in enumerate(emb_ocr.regions):
                            page_regions.append(ExtractedRegion(
                                id=f"docx_fig{img_idx+1}_t{t_idx+1}",
                                bbox=t_reg.bbox,
                                text=t_reg.text,
                                category="text",
                                confidence=t_reg.confidence,
                                source=ExtractionSource.PADDLE_OCR
                            ))
                except Exception as docx_img_err:
                    log(f"[NexusOCR] [Warning] DOCX embedded image #{img_idx+1} error: {docx_img_err}")

        full_md = data["markdown"]
        if embedded_cards:
            full_md += "\n\n" + "\n\n".join(embedded_cards)

        total_ms = (time.perf_counter() - start_time) * 1000.0
        form_data = FormDataExtractor.extract_form_data(full_md)

        page = PageResult(
            page_number=1,
            width=800,
            height=1100,
            is_digital=True,
            trust_score=1.0,
            regions=page_regions,
            markdown=full_md,
            source=ExtractionSource.DIGITAL_NATIVE,
            execution_time_ms=total_ms,
        )

        return DocumentResult(
            file_name=file_name,
            total_pages=1,
            format="DOCX",
            pages=[page],
            full_markdown=full_md,
            structured_json={
                "file": file_name,
                "total_pages": 1,
                "format": "DOCX",
                "total_paragraphs": data.get("total_paragraphs", 0),
                "total_tables": data.get("total_tables", 0),
                "form_data": form_data,
            },
            average_trust_score=1.0,
            total_execution_time_ms=total_ms,
        )

    def _process_spreadsheet_file(self, file_path: str, options: ProcessingOptions) -> DocumentResult:
        """Processes Excel .xlsx and CSV files into structured tables and markdown."""
        file_name = Path(file_path).name
        start_time = time.perf_counter()
        data = SpreadsheetProcessor.extract_spreadsheet(file_path)
        total_ms = (time.perf_counter() - start_time) * 1000.0
        full_md = data["markdown"]
        form_data = FormDataExtractor.extract_form_data(full_md)

        total_sheets = len(data.get("sheets", [])) or 1
        table_structures: List[TableStructure] = []
        for t in data.get("tables", []):
            table_structures.append(TableStructure(
                id=t.get("id", "table_1"),
                bbox=BoundingBox(xmin=0, ymin=0, xmax=1000, ymax=800),
                num_rows=t.get("num_rows", 0),
                num_cols=t.get("num_cols", 0),
                markdown=t.get("markdown", ""),
                html="",
            ))

        page = PageResult(
            page_number=1,
            width=1000,
            height=800,
            is_digital=True,
            trust_score=1.0,
            tables=table_structures,
            markdown=full_md,
            source=ExtractionSource.DIGITAL_NATIVE,
            execution_time_ms=total_ms,
        )

        return DocumentResult(
            file_name=file_name,
            total_pages=total_sheets,
            pages=[page],
            full_markdown=full_md,
            structured_json={
                "file": file_name,
                "total_pages": total_sheets,
                "format": "SPREADSHEET",
                "sheets": data.get("sheets", []),
                "tables": data.get("tables", []),
                "form_data": form_data,
            },
            average_trust_score=1.0,
            total_execution_time_ms=total_ms,
        )

    def _process_presentation_file(self, file_path: str, options: ProcessingOptions) -> DocumentResult:
        """Processes PowerPoint .pptx files slide-by-slide with embedded image captioning & OCR."""
        file_name = Path(file_path).name
        start_time = time.perf_counter()
        data = PresentationProcessor.extract_presentation(file_path)
        total_ms = (time.perf_counter() - start_time) * 1000.0

        pages: List[PageResult] = []
        for s in data.get("slides", []):
            slide_md = s["markdown"]
            slide_regions: List[ExtractedRegion] = []
            slide_images = s.get("embedded_images", [])

            if options.enable_ocr and slide_images:
                img_cards = []
                for img_idx, img_bytes in enumerate(slide_images):
                    try:
                        img_np = ImageProcessor.load_image(img_bytes)
                        ih, iw = img_np.shape[:2]
                        if iw < 40 or ih < 40:
                            continue
                        desc = ImageProcessor.describe_image(img_np)
                        caption = desc.get("caption", f"Slide {s['slide_number']} Image #{img_idx+1}")
                        color_str = "Monochrome / Grayscale" if desc.get("is_monochrome") else "Full Color"

                        emb_ocr = self.paddle_engine.process_page_image(img_np, page_num=img_idx + 1)
                        ocr_text = emb_ocr.markdown if (emb_ocr and emb_ocr.markdown and not emb_ocr.markdown.startswith("*(")) else ""

                        card_lines = [
                            f"### Slide Image #{img_idx+1}",
                            f"> **Visual Caption**: {caption}",
                            f"> - **Dimensions**: {iw}x{ih} px",
                            f"> - **Color Profile**: {color_str}",
                        ]
                        if ocr_text:
                            card_lines.append(">\n> **Extracted Text from Image**:\n" + "\n".join(f"> {l}" for l in ocr_text.splitlines()))

                        img_cards.append("\n".join(card_lines))

                        slide_regions.append(ExtractedRegion(
                            id=f"slide{s['slide_number']}_fig_{img_idx+1}",
                            bbox=BoundingBox(xmin=50, ymin=50, xmax=min(1230, 50 + iw), ymax=min(670, 50 + ih)),
                            text=f"[Slide Image #{img_idx+1}: {caption}]",
                            category="figure",
                            confidence=0.95,
                            source=ExtractionSource.DOCLING_LAYOUT
                        ))

                        if emb_ocr and emb_ocr.regions:
                            for t_idx, t_reg in enumerate(emb_ocr.regions):
                                slide_regions.append(ExtractedRegion(
                                    id=f"slide{s['slide_number']}_fig{img_idx+1}_t{t_idx+1}",
                                    bbox=t_reg.bbox,
                                    text=t_reg.text,
                                    category="text",
                                    confidence=t_reg.confidence,
                                    source=ExtractionSource.PADDLE_OCR
                                ))
                    except Exception as ppt_img_err:
                        log(f"[NexusOCR] [Warning] PPTX slide {s['slide_number']} image error: {ppt_img_err}")

                if img_cards:
                    slide_md += "\n\n" + "\n\n".join(img_cards)

            pages.append(PageResult(
                page_number=s["slide_number"],
                width=1280,
                height=720,
                is_digital=True,
                trust_score=1.0,
                regions=slide_regions,
                markdown=slide_md,
                source=ExtractionSource.DIGITAL_NATIVE,
                execution_time_ms=total_ms / max(1, len(data.get("slides", []))),
            ))

        full_md = "\n\n---\n\n".join(p.markdown for p in pages)
        if not pages:
            pages.append(PageResult(page_number=1, width=1280, height=720, markdown=full_md))

        form_data = FormDataExtractor.extract_form_data(full_md)

        serialized_slides = []
        for s in data.get("slides", []):
            serialized_slides.append({
                "slide_number": s.get("slide_number", 1),
                "title": s.get("title", ""),
                "text": s.get("text", ""),
                "markdown": s.get("markdown", ""),
                "embedded_images_count": len(s.get("embedded_images", [])),
            })

        return DocumentResult(
            file_name=file_name,
            total_pages=len(pages),
            format="PRESENTATION",
            pages=pages,
            full_markdown=full_md,
            structured_json=_sanitize_for_json({
                "file": file_name,
                "total_pages": len(pages),
                "format": "PRESENTATION",
                "slides": serialized_slides,
                "form_data": form_data,
            }),
            average_trust_score=1.0,
            total_execution_time_ms=total_ms,
        )

    def _process_text_markup_file(self, file_path: str, options: ProcessingOptions) -> DocumentResult:
        """Processes plain text, Markdown, and HTML/XML documents."""
        file_name = Path(file_path).name
        ext = Path(file_path).suffix.lower()
        start_time = time.perf_counter()

        if ext in (".html", ".htm", ".xml"):
            data = TextMarkupProcessor.extract_html(file_path)
        else:
            data = TextMarkupProcessor.extract_plain_text(file_path)

        total_ms = (time.perf_counter() - start_time) * 1000.0
        full_md = data["markdown"]
        form_data = FormDataExtractor.extract_form_data(full_md)

        table_structures: List[TableStructure] = []
        for t in data.get("tables", []):
            table_structures.append(TableStructure(
                id=t.get("id", "html_table_1"),
                bbox=BoundingBox(xmin=0, ymin=0, xmax=800, ymax=1000),
                num_rows=t.get("num_rows", 0),
                num_cols=t.get("num_cols", 0),
                markdown=t.get("markdown", ""),
                html="",
            ))

        page = PageResult(
            page_number=1,
            width=800,
            height=1000,
            is_digital=True,
            trust_score=1.0,
            tables=table_structures,
            markdown=full_md,
            source=ExtractionSource.DIGITAL_NATIVE,
            execution_time_ms=total_ms,
        )

        return DocumentResult(
            file_name=file_name,
            total_pages=1,
            pages=[page],
            full_markdown=full_md,
            structured_json={
                "file": file_name,
                "total_pages": 1,
                "format": ext.upper().lstrip("."),
                "form_data": form_data,
            },
            average_trust_score=1.0,
            total_execution_time_ms=total_ms,
        )

    def _process_epub_file(self, file_path: str, options: ProcessingOptions) -> DocumentResult:
        """Processes EPUB digital books."""
        file_name = Path(file_path).name
        start_time = time.perf_counter()
        data = TextMarkupProcessor.extract_epub(file_path)
        total_ms = (time.perf_counter() - start_time) * 1000.0
        full_md = data["markdown"]
        total_p = data.get("total_pages", 1)

        page = PageResult(
            page_number=1,
            width=800,
            height=1000,
            is_digital=True,
            trust_score=1.0,
            markdown=full_md,
            source=ExtractionSource.DIGITAL_NATIVE,
            execution_time_ms=total_ms,
        )

        return DocumentResult(
            file_name=file_name,
            total_pages=total_p,
            pages=[page],
            full_markdown=full_md,
            structured_json={
                "file": file_name,
                "total_pages": total_p,
                "format": "EPUB",
            },
            average_trust_score=1.0,
            total_execution_time_ms=total_ms,
        )
