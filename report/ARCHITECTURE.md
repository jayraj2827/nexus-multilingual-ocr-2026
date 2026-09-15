# NexusOCR System Architecture & Component Design

**NexusOCR: Multilingual Document OCR Extraction Pipeline**  
*Adaptive Multilingual Document Intelligence Engine*  
*Developed for Nexus Hackathon 2026 (GLS University, Ahmedabad) by Harsh Aalwani & Jayraj Prajapati.*

This document details the architectural foundation of **NexusOCR**, explaining the design philosophy, layer responsibilities, boundaries, and how the hybrid architecture ensures modularity, high performance, and backward compatibility.

---

## 1. Architectural Philosophy: Why a Hybrid Architecture?

In document intelligence systems, architectures typically drift toward one of two extremes:
1. **Flat / Monolithic Layers**: All OCR logic, format manipulation, and API routes sit in giant scripts. Adding a new modality creates spaghetti code.
2. **Over-Abstracted Pipeline Engines**: Generic pipelines where everything is a black box, making fast-path optimizations (like skipping GPU inference for digital PDFs in <30ms) cumbersome and hard to trace.

### The Hybrid Feature-Oriented Solution
NexusOCR adopts a **Hybrid Architecture** combining:
- **Centralized Pipeline Execution Runtime (`pipeline/`)**: Handles execution mechanics, stage lifecycle, progress reporting, timeout/cancellation, and error propagation.
- **Feature-Oriented Domain Modules (`features/`)**: High-level domain workflows (`document_ocr`, `layout`, `vision`, `translation`, `batch`) that own business rules, strategy routing, form field extraction, and result formatting.
- **Reusable Media Processors (`processors/`)**: Pure technical operations on files and byte streams (PDF rasterization, image transformations & multi-page TIFF splitting, Office DOCX/XLSX/PPTX parsing, text/markup reading) without domain logic.
- **Engine Adapters (`engines/`)**: Strict encapsulation of external libraries, third-party frameworks, and hardware drivers (`PaddleOCR`, `PyMuPDF`, `Docling`, `CUDA`).
- **Strict Data & Format Contracts (`contracts/`)**: Versioned Pydantic models guaranteeing type safety across layers and format capability matrices (`formats.py`).
- **Dedicated External Interfaces (`interfaces/`)**: Clean REST routes (FastAPI), command-line entry points (CLI), and Python SDK bindings.

---

## 2. Layer Breakdown & Boundaries

```
nexusocr/
├── pipeline/       ──> Execution Mechanics Only (Runner, Stage, Context, Metrics)
├── features/       ──> Domain Intelligence (Routing, Result Assembly, Form Extraction, Batch)
├── processors/     ──> Media I/O & Byte Manipulation (PDF, Image, Office, Text/Markup)
├── engines/        ──> Hardware & Framework Adapters (PyMuPDF, PaddleOCR, Docling)
├── contracts/      ──> Typed Data Contracts, Formats & Schemas (Pydantic Models)
├── interfaces/     ──> Entry Points (FastAPI API, CLI, Python SDK Client)
├── config.py       ──> Centralized Constants, Thresholds & Paths
├── logging.py      ──> Unified Console & Stage Diagnostics
└── exceptions.py   ──> Standardized Exception Hierarchy
```

### 2.1 `pipeline/` (Execution Mechanics)
The `pipeline` package is domain-agnostic. It does not know what an OCR engine or a document is. Its responsibilities are strictly operational:
- **`runner.py` (`PipelineRunner`)**: Manages the ordered registration and sequential execution of stages. Evaluates cancellation flags before dispatching each stage.
- **`context.py` (`ProcessingContext`)**: Stateful blackboard flowing through the pipeline. Manages run-level timers, options, intermediate artifacts, cancellation tokens, and progress callbacks.
- **`stage.py` (`PipelineStage`)**: Base class defining stage lifecycle hooks:
  - `initialize()`: Lazy resource acquisition before processing.
  - `can_handle(context)`: Predicate checking whether the stage applies to the input.
  - `process(context)`: Concrete execution boundary.
  - `cleanup(context)`: Safe release of temporary resources.
- **`execution.py` (`StageExecutor`)**: Protects execution bounds, measures microsecond latency, records stage status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`), and wraps unexpected exceptions into `StageExecutionError`.

### 2.2 `features/` (Domain-Specific Intelligence)
Features own user-facing document processing capabilities and domain heuristics:
- **`features/document_ocr/`**:
  - `service.py` (`DocumentOCRService`): Executes the end-to-end multi-format document processing loop across PDF, raster & multi-frame images (TIFF), Word (.docx), Excel (.xlsx/.csv), PowerPoint (.pptx), text/markup (.txt, .html, .epub), orchestrating Tier 1 (PyMuPDF / direct parsing) and Tier 2 (PaddleOCR).
  - `forms.py` (`FormDataExtractor`): Extracts key-value pairs, monetary amounts, dates, and entity identifiers from extracted content.
  - `stage.py` (`DocumentOCRStage`): Adapts `DocumentOCRService` into a pluggable `PipelineStage`.
- **`features/batch.py` (`BatchDocumentService`)**: Isolated multi-document batch queue processing with individual item error containment and overall execution summaries.
- **`features/layout/`**: Owns table reconstruction, multi-column reading order, and IBM Docling integration (`LayoutService`, `LayoutStage`).
- **`features/vision/`**: Computes image brightness, contrast std-dev, color distribution, bounding-box cropping, and JPEG thumbnail generation (`VisionService`, `VisionStage`).
- **`features/translation/`**: Unicode block language detection (Devanagari, Gujarati, Latin) and multilingual text translation (`TranslationService`, `TranslationStage`).

### 2.3 `processors/` (Technical Media Handlers)
- **`processors/pdf.py`**: Wraps PyMuPDF document handles, page-count inspection, DPI rendering, and embedded Pixmap extraction.
- **`processors/image.py`**: OpenCV and Pillow routines for image normalization, bounding-box cropping, and multi-frame TIFF parsing.
- **`processors/office.py`**: OpenXML parsers for Word (`.docx`), Excel (`.xlsx`, `.csv`), and PowerPoint (`.pptx`).
- **`processors/text_markup.py`**: Plain text, HTML, and EPUB structured reading.

### 2.4 `engines/` (Encapsulation of External Libraries)
- **`engines/ocr/pymupdf.py`**: Evaluates digital font descriptors, computes the trust score, and extracts native vector text.
- **`engines/ocr/paddleocr.py`**: Wraps PaddleOCR detection (DBNet) and recognition (SVTR/CRNN) models, supporting both CPU AVX and NVIDIA CUDA execution.
- **`engines/ocr/docling.py`**: Adapts IBM Docling's DocumentConverter and TableFormer models.
- **`engines/vision/base.py`**: Base interface and OpenCV implementation for visual profiling.
- **`engines/translation/base.py`**: Unicode block detection for Indic and Latin scripts.

### 2.5 `contracts/` (Pydantic Data Contracts)
- **`formats.py`**: Central registry of supported extensions, MIME categories, and defensive media rejection rules.
- **`results.py`**: Canonical data schemas: `BoundingBox`, `ExtractedRegion`, `TableStructure`, `PageResult`, `DocumentResult`.
- **`input.py`**: Typed options: `ProcessingOptions`, `DocumentInput`.

### 2.6 `interfaces/` (Client Gateways)
- **`interfaces/api/`**: FastAPI REST application exposing `/api/process`, `/api/batch`, `/api/page_image`, `/api/samples`, `/api/formats`, `/api/health`.
- **`interfaces/cli/`**: Terminal CLI runner (`python -m nexusocr process`, `formats`, `health`, `serve`).
- **`interfaces/sdk/`**: High-level programmatic client (`NexusOCRClient`).

---

## 3. Backward Compatibility Architecture

NexusOCR preserves 100% backward compatibility with legacy scripts through lightweight compatibility bridges:
- `app.py` re-exports the FastAPI app from `nexusocr.interfaces.api.app`.
- `pipeline.py` re-exports `NexusOCRPipeline` delegating directly to `DocumentOCRService`.
- `config.py` in the root delegates to `nexusocr.config`.
- `engine/` modules re-export legacy contracts and engine classes without code duplication.
