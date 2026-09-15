# NexusOCR Code Flow & Execution Tracing

**NexusOCR: Multilingual Document OCR Extraction Pipeline**  
*Adaptive Multilingual Document Intelligence Engine*  
*Nexus Hackathon 2026 (GLS University, Ahmedabad)*

This document provides step-by-step code execution traces, sequence diagrams, and mathematical routing heuristics for all workflows across NexusOCR.

---

## 1. Web UI & REST API Execution Flow

When a user submits a document into the NexusOCR Web UI or sends a request to `POST /api/process`, execution proceeds as follows:

```
[ User Upload ] ──► [ POST /api/process ] ──► [ FormatResolver.validate_file() ]
                                                         │
                                               [ Save to data/uploads/ ]
                                                         │
                                                         ▼
                                            [ DocumentOCRService.process_document() ]
                                                         │
                             ┌───────────────────────────┴───────────────────────────┐
                             │ Category == PDF                                       │ Category != PDF
                             ▼                                                       ▼
                [ Service.process_pdf() ]                               [ Specialized Processor ]
                             │                                           (Office, Image, Markup)
                ┌────────────┴────────────┐
                │ Loop each page (1 to N) │
                ▼                         ▼
      [ extract_digital_page() ]
      (PyMuPDF Font & Glyph Check)
                │
     ┌──────────┴──────────┐
     │ Trust >= 0.85       │ Trust < 0.85
     ▼                     ▼
[ Tier 1 Digital ]   [ 150 DPI Rasterize ]
(~11 ms, 0MB VRAM)         │
                     ▼
             [ Tier 2 PaddleOCR ]
             (DBNet + Indic SVTR)
             (~150-400ms GPU / ~1.08s CPU)
     │                     │
     └──────────┬──────────┘
                │
                ▼
   [ FormDataExtractor.extract_form_data() ]
   [ DefaultTranslationEngine.detect_language() ]
                │
                ▼
   [ Assemble Canonical DocumentResult ] ──► [ HTTP 200 JSON ] ──► [ UI Dual-Pane View ]
```

---

## 2. 2-Tier Adaptive Routing & Trust Scoring Mechanics

The core optimization of NexusOCR is its **2-Tier Adaptive Document Profiler**. It allows high-density digital PDFs (such as financial reports, attendance lists, or statements) to extract in **~11 ms to 30 ms** with zero GPU VRAM consumption, while seamlessly routing degraded scans, mixed scripts, or flattened images to neural vision OCR.

### Mathematical Trust Formula
The decision is calculated per-page inside `nexusocr/engines/ocr/pymupdf.py`:

$$	ext{printable\_ratio} = 1.0 - \left(rac{	ext{non\_printable\_chars}}{	ext{total\_chars}}ight)$$

$$	ext{density\_score} = \min\left(1.0, rac{	ext{total\_chars}}{40.0}ight)$$

$$	ext{trust\_score} = (0.85 	imes 	ext{printable\_ratio}) + (0.15 	imes 	ext{density\_score})$$

- **If $	ext{trust\_score} \ge 0.85$:** Route to **Tier 1 (PyMuPDF Fast-Path)**.
- **If $	ext{trust\_score} < 0.85$:** Route to **Tier 2 (PaddleOCR Deep Vision)**.

---

## 3. Multi-Format Processing Workflows

### 3.1 Office Documents (DOCX, XLSX, PPTX)
1. `FormatResolver.validate_file()` detects Office category.
2. `DocxProcessor`: Parses paragraphs, heading styles (`heading 1`, `heading 2`), lists, and tables via `python-docx`.
3. `SpreadsheetProcessor`: Reads worksheets, headers, and rows via `openpyxl` / `csv`, exporting formatted Markdown tables.
4. `PresentationProcessor`: Traverses slides, shape frames, tables, and embedded images via `python-pptx`.
5. Output is wrapped into a unified `DocumentResult` with 100% exact digital trust score.

### 3.2 Raster Images & Multi-Frame TIFF
1. `ImageProcessor.load_image()` decodes image buffers using OpenCV.
2. Multi-page TIFF files are demuxed into individual frames using Pillow `ImageSequence`.
3. Each frame is sent to `PaddleOCREngine.process_page_image()`.
4. Extracted lines, bounding boxes, and confidence scores are aggregated into `PageResult` objects.

### 3.3 Defensive Media Rejection Flow
1. When an incoming file has an audio (`.mp3`, `.wav`) or video (`.mp4`, `.mkv`, `.avi`) extension or MIME type:
2. `FormatResolver.validate_file()` matches `UNSUPPORTED_MEDIA`.
3. An `UnsupportedFormatError` is raised immediately in **$< 2	ext{ ms}$**.
4. FastAPI returns HTTP 400 with a descriptive error message, protecting system RAM and GPU resources.
