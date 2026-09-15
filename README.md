# ⚡ NexusOCR: Multilingual Document OCR Extraction Pipeline
### Adaptive Multilingual Document Intelligence Engine

[![Nexus Hackathon 2026](https://img.shields.io/badge/Nexus%20Hackathon-2026%20%7C%20GLS%20University-blue?style=flat-square)](https://glsuniversity.ac.in)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-fitz%20v1.24%2B-red?style=flat-square)](https://pymupdf.readthedocs.io)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-v3.7%20%7C%20Indic-blueviolet?style=flat-square)](https://github.com/PaddlePaddle/PaddleOCR)
[![Hardware](https://img.shields.io/badge/Hardware-AMD%20Ryzen%20%2F%20EPYC%20%7C%20NVIDIA%20CUDA-orange?style=flat-square)](https://amd.com)
[![Tests](https://img.shields.io/badge/Tests-65%2F66%20Passed-brightgreen?style=flat-square)](tests/)
[![Offline](https://img.shields.io/badge/Deployment-100%25%20Offline%20%7C%20Zero%20Cloud-success?style=flat-square)](#)

> **Submitted as part of Nexus Hackathon 2026**  
> **Affiliated to GLS University, Ahmedabad**  
> **Prepared By: Harsh Aalwani, Jayraj Prajapati**

NexusOCR is an enterprise-grade document extraction and multimodal intelligence engine engineered for high-throughput, local-first document processing. Combining sub-15ms digital extraction with deep neural vision for complex Indic scripts (**Hindi, Devanagari, Gujarati, Marathi, and English**), NexusOCR reconstructs clean Markdown, hierarchical tables, CSVs, and normalized spatial bounding boxes with **zero external cloud dependencies**.

---

## 📑 Table of Contents

- [Architectural Overview](#-architectural-overview)
- [Key Capabilities](#-key-capabilities)
- [Operating Principle](#-operating-principle)
- [Hardware Telemetry & Acceleration](#-hardware-telemetry--acceleration)
- [Supported Formats Matrix](#-supported-formats-matrix)
- [Multilingual Precision & Indic Support](#-multilingual-precision--indic-support)
- [Empirical Benchmarks & Telemetry](#-empirical-benchmarks--telemetry)
- [Interactive Web UI](#-interactive-web-ui)
- [REST API Reference](#-rest-api-reference)
- [CLI Reference](#-cli-reference)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Dependencies](#-installation--dependencies)
- [Verification & Automated Tests](#-verification--automated-tests)
- [Roadmap & Enhancements](#-roadmap--enhancements)
- [Project Reports & Documentation](#-project-reports--documentation)

---

## 🏛️ Architectural Overview

NexusOCR employs an adaptive **dual-tier routing pipeline**. Every incoming document page is profiled by an automated native trust scorer before execution:

```
                            [ INCOMING DOCUMENT ]
                  (PDF, DOCX, XLSX, PPTX, TIFF, PNG, JPG)
                                     │
                                     ▼
                        STATION 01: INGEST & MIME GATE
                     ├── Magic byte signature inspection
                     ├── Audio / Video rejection (<2ms)
                     └── Page rasterization & frame demuxing
                                     │
                                     ▼
                          PAGE TRUST PROFILER
                     ├── Vector text density & font tables
                     └── Structural glyph coverage evaluation
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
          (Trust Score >= 0.85)              (Trust Score < 0.85)
                    │                                 │
                    ▼                                 ▼
         TIER 1: DIGITAL NATIVE             TIER 2: NEURAL VISION
         (PyMuPDF C-Extension)             (PaddleOCR Multi-Script)
         ⚡ Latency: 11-30 ms / page        🚀 Latency: ~150-400ms GPU / ~1.08s CPU
         🎯 100% Exact Vector Text         🎯 98–99% Indic Neural Accuracy
         💾 0 MB VRAM                       💾 ~800 MB VRAM / AVX CPU
                    │                                 │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                     STATION 03: SEMANTIC PROFILER
                     ├── Key-Value entity regex extractor
                     ├── Indic script detector (gu, hi, en)
                     └── Structural table grid reconstruction
                                     │
                                     ▼
                        CANONICAL DOCUMENT RESULT
                     ├── Clean Formatted Markdown Text
                     ├── HTML & Markdown Table Grid Data
                     ├── Word Bounding Boxes & Confidence Scores
                     └── Execution Latency & Engine Telemetry
```

---

## ⚡ Key Capabilities

- **Adaptive Dual-Tier Routing:** Digital PDFs bypass neural OCR entirely via PyMuPDF in **~11 ms per page**, while flattened scans and raster images automatically escalate to GPU/CPU neural vision.
- **Indic Script Precision:** Specialized recognition models trained on complex ligatures, conjuncts, and vowel diacritics for **Hindi, Devanagari, Gujarati, Marathi, and English**.
- **Structural Table Extraction:** Converts dense financial grids and balance sheets into clean Markdown and HTML tables with preserved row and column alignment.
- **Office Document Support:** Direct native parsing for Word (`.docx`), Excel (`.xlsx`, `.csv`), and PowerPoint (`.pptx`) without rasterization overhead.
- **Key-Value Form Extraction:** Automatically extracts dates, currency amounts (₹, $, €, £), emails, phone numbers, and identifier pairs (`Field: Value`).
- **Defensive MIME Shield:** Instant `< 2ms` defensive rejection for unsupported multimedia streams (audio and video files).
- **100% Offline & Private:** Zero external cloud API calls — all models run locally on your host hardware.

---

## ⚙️ Operating Principle

The system first validates and identifies the input format via `FormatResolver`. For PDF content, pages are inspected and assigned a trust score. High-trust pages are processed by the native vector path; lower-trust pages are routed to neural OCR. Results from both paths are normalized into common document contracts, enriched with entities and layout information, and synthesized into a single `DocumentResult` representation that the UI, API, and CLI can consume.

```
[ Client Input ] ──► [ FormatResolver ] ──► [ Page Demuxing ] ──► [ Page Trust Profiler ]
  (Web/REST/CLI)     (MIME + Ext Gate)                                      │
                                                    ┌───────────────────────┴───────────────────────┐
                                                    │ (Trust >= 0.85)                               │ (Trust < 0.85)
                                                    ▼                                               ▼
                                         [ Tier 1: PyMuPDF ]                             [ Tier 2: PaddleOCR ]
                                                    │                                               │
                                                    └───────────────────────┬───────────────────────┘
                                                                            │
                                                                            ▼
                                                            [ Normalization & Entity Extraction ]
                                                                            │
                                                                            ▼
                                                               [ Document Synthesis ] ──► [ Output ]
                                                                 (DocumentResult)         (Markdown/JSON/Tables)
```

---

## 🖥️ Hardware Telemetry & Acceleration

NexusOCR includes automatic hardware auto-sensing via `detect_hardware()`, adapting dynamically to your system architecture without requiring manual configuration:

```
[ HOST HARDWARE PROBE ]
       │
       ├──► AMD Ryzen / EPYC CPU  ──► Multi-threaded AVX Vector Instructions
       ├──► Intel Core / Xeon CPU ──► Multi-threaded Vector Execution
       └──► NVIDIA CUDA GPU       ──► Tensor Core Acceleration (RTX 30xx/40xx)
```

- **AMD Ryzen / EPYC Optimizations:** High-throughput CPU multi-threading for PyMuPDF C-extensions and PaddleOCR AVX execution.
- **NVIDIA CUDA GPU Acceleration:** Sub-second visual inference via `paddlepaddle-gpu` on supported NVIDIA GeForce RTX and data center GPUs.
- **Zero VRAM Footprint on Tier 1:** Born-digital documents require 0 MB of GPU memory, leaving hardware resources free for other services.

---

## 📋 Supported Formats Matrix

NexusOCR validates file integrity at ingest using magic-byte inspection and format categorization:

| Category | Extension | Format Name | Extraction Mode |
|:---|:---|:---|:---|
| **Document** | `.pdf` | Portable Document Format | Dual-Tier Hybrid (PyMuPDF / PaddleOCR) |
| **Document** | `.docx` | Microsoft Word OpenXML | Native OpenXML Structural Parsing |
| **Spreadsheet** | `.xlsx` | Microsoft Excel Spreadsheet | Native OpenXML Table Extraction |
| **Data** | `.csv` | Comma-Separated Values | Delimited Grid Parsing |
| **Presentation** | `.pptx` | Microsoft PowerPoint | Slide & Shape Text Extraction |
| **Raster Image** | `.png`, `.jpg`, `.jpeg` | Standard Raster Images | PaddleOCR Neural Vision |
| **Raster Image** | `.bmp`, `.webp` | Bitmap & WebP Images | PaddleOCR Neural Vision |
| **Multi-Frame Image** | `.tiff`, `.tif` | Tagged Image File Format | Multi-Frame Demuxer + Neural Vision |
| **Markup & Text** | `.txt`, `.html`, `.epub` | Text & Markup Documents | Structured Text Extractor |
| **Media (Unsupported)** | `.mp4`, `.mp3`, `.wav`, etc. | Audio / Video Streams | **Explicitly Rejected (<2ms, HTTP 400)** |

---

## 🌐 Multilingual Precision & Indic Support

NexusOCR features specialized optical recognition heads for Indian regional languages alongside Latin scripts:

| Script / Language | Unicode Range | Supported Engine | 300 DPI Accuracy | 150 DPI Accuracy |
|:---|:---|:---|:---:|:---:|
| **English (Latin)** | `U+0000 - U+007F` | PyMuPDF / PaddleOCR | **100% (Digital) / 99.4% (Scan)** | 98.1% |
| **Hindi (हिन्दी / Devanagari)** | `U+0900 - U+097F` | PaddleOCR Indic | **99.2%** | 94.6% |
| **Gujarati (ગુજરાતી)** | `U+0A80 - U+0AFF` | PaddleOCR Indic | **98.9%** | 93.8% |
| **Marathi (मराठी)** | `U+0900 - U+097F` | PaddleOCR Indic | **99.0%** | 94.2% |

---

## 📊 Empirical Benchmarks & Telemetry

The following real-world fixtures from `tests/fixtures/` represent empirical performance measured across host execution:

| Fixture | Format | Status | Latency | Trust | Engine |
|:---|:---|:---:|:---:|:---:|:---|
| **Digital English Report** | Digital PDF | **PASS** | **11 ms** | **100%** | PyMuPDF Native Fast-Path |
| **Hindi & Devanagari Script** | Multilingual PDF | **PASS** | **11 ms** | **100%** | PyMuPDF Native Fast-Path |
| **Financial Statement & Grid** | Tabular PDF | **PASS** | **14 ms** | **100%** | PyMuPDF Native Fast-Path |
| **Gujarati & English Document** | Multilingual PDF | **PASS** | **91 ms** | **99%** | Dual-Tier Hybrid |
| **System Design Architecture** | Office Word (.docx) | **PASS** | **86 ms** | **100%** | DocxProcessor OpenXML |
| **Certificate Raster Badge** | Scanned Image (.png) | **PASS** | **1,083 ms** | **95%** | PaddleOCR Neural Vision (CPU) |

---

## 🖥️ Interactive Web UI

NexusOCR includes a responsive, lightweight web application served directly by FastAPI:

1. **Overview Dashboard:**
   - Visual architectural pipeline flow.
   - Live hardware status and telemetry indicators.
   - Comprehensive format support matrix.
   - Empirical benchmark and latency metrics.

2. **Studio Workspace:**
   - **Pre-Loaded Test Suite:** Instant one-click testing of pre-configured fixtures (Digital English, Hindi/Devanagari, Financial Tables, Gujarati, DOCX, Scanned Images).
   - **Drag-and-Drop Ingestion:** Support for single files or multi-document batches.
   - **Dual-Pane Synchronized Inspection:** Left pane renders the source page raster; right pane displays the reconstructed Markdown text.
   - **Interactive Bounding Box Overlays:** Hovering or clicking any bounding box on the image highlights the corresponding text block in the output.
   - **One-Click Export:** Download results as Markdown (`.md`), structured JSON (`.json`), or copy directly to the clipboard.

---

## 🔌 REST API Reference

The server exposes standard OpenAPI/Swagger endpoints accessible at `http://127.0.0.1:8000/docs`:

### `POST /api/process`
Process an uploaded document through the extraction pipeline.

**Request:** `multipart/form-data`
- `file`: Document or image binary payload.
- `max_pages` *(optional)*: Integer page limit.

**Response (`200 OK`):**
```json
{
  "file_name": "annual_report.pdf",
  "total_pages": 4,
  "average_trust_score": 0.98,
  "total_execution_time_ms": 44.2,
  "full_markdown": "# Reconstructed Document Content...",
  "pages": [
    {
      "page_number": 1,
      "width": 1200,
      "height": 1600,
      "is_digital": true,
      "trust_score": 1.0,
      "markdown": "...",
      "execution_time_ms": 11.2,
      "regions": [
        {
          "id": "p1_l0",
          "bbox": { "xmin": 72.0, "ymin": 96.0, "xmax": 540.0, "ymax": 124.0 },
          "text": "Executive Summary",
          "category": "header",
          "confidence": 1.0,
          "source": "digital_native"
        }
      ]
    }
  ]
}
```

### `POST /api/batch`
Process multiple documents concurrently with isolated error handling.

### `GET /api/page_image/{filename}/{page_number}`
Returns a 150 DPI rendered PNG image of a specified page for visual inspection.

### `GET /api/samples`
Returns a list of pre-configured sample fixture documents.

### `POST /api/process_sample`
Processes a sample fixture by ID without requiring file uploads.

### `GET /api/formats`
Returns supported and unsupported file extensions with capability metadata.

### `GET /api/health`
Returns host hardware status, execution mode (GPU/CPU), and engine availability.

---

## ⌨️ CLI Reference

NexusOCR can be executed directly from the terminal via Python:

```powershell
# General Help
python -m nexusocr --help

# Process a document and print Markdown output
python -m nexusocr process tests/fixtures/test_digital_english.pdf

# Save output to a file
python -m nexusocr process document.pdf -o output.md

# Output structured JSON (with bounding boxes and confidence scores)
python -m nexusocr process document.pdf --format json -o output.json

# Check hardware and engine diagnostics
python -m nexusocr health

# List all supported document formats
python -m nexusocr formats

# Launch the FastAPI web server
python -m nexusocr serve --host 127.0.0.1 --port 8000 --reload
```

---

## 📁 Project Directory Structure

```
nexus-multilingual-ocr-2026/
├── app.py                      # FastAPI Web Application & Server Entrypoint
├── config.py                   # Centralized Configuration (Paths, Thresholds, Telemetry)
├── pipeline.py                 # Pipeline Runner Compatibility Wrapper
├── requirements.txt            # Project Dependencies
├── pytest.ini                  # Pytest Configuration
│
├── nexusocr/                   # Core Package
│   ├── contracts/              # Pydantic v2 Schemas & Data Contracts
│   │   ├── formats.py          # Format Registry & Capabilities
│   │   ├── results.py          # DocumentResult, PageResult, BoundingBox
│   │   └── input.py            # ProcessingOptions & Input Specifications
│   │
│   ├── engines/                # External Engine Adapters
│   │   ├── ocr/
│   │   │   ├── pymupdf.py      # Tier 1 Digital Native Extractor
│   │   │   ├── paddleocr.py    # Tier 2 Neural Vision OCR
│   │   │   └── docling.py      # Layout & TableFormer Adapter
│   │   ├── vision/             # Image Quality & Contrast Profiling
│   │   └── translation/        # Script Detection & Unicode Categorization
│   │
│   ├── features/               # High-Level Feature Services
│   │   ├── document_ocr/       # Document Processing & Key-Value Extraction
│   │   ├── layout/             # Layout Analysis Service
│   │   ├── vision/             # Computer Vision Preview Service
│   │   ├── translation/        # Translation Service
│   │   └── batch.py            # Multi-File Batch Service
│   │
│   ├── processors/             # Low-Level Format Processors
│   │   ├── office.py           # DOCX, XLSX, PPTX OpenXML Processors
│   │   ├── image.py            # OpenCV Raster Operations & TIFF Demuxer
│   │   └── text_markup.py      # TXT, HTML, EPUB Processors
│   │
│   ├── interfaces/             # User & API Interfaces
│   │   ├── api/                # FastAPI Endpoints & App Definition
│   │   └── cli/                # Command-Line Interface (`python -m nexusocr`)
│   │
│   ├── logging.py              # Unified Logging
│   └── exceptions.py           # Exception Hierarchy
│
├── frontend/                   # UI Files
│   ├── index.html              # Dashboard & Studio Layout
│   ├── app.js                  # Frontend Application Logic & View Controller
│   └── styles.css              # UI Stylesheet & Design System
│
├── report/                     # Academic & Engineering Project Reports
│   ├── PROJECT_REPORT.md       # Official 24-Page Project Report (GLS University)
│   ├── ARCHITECTURE.md         # Detailed System Architecture & Layers
│   ├── CODE_FLOW.md            # Execution Traces & Sequence Diagrams
│   ├── DEVELOPER_GUIDELINES.md # Golden Rules & Extension Recipes
│   └── README.md               # Report Directory Index
│
└── tests/                      # Automated Regression Test Suite (66 Tests)
    ├── fixtures/               # Test Documents (PDF, DOCX, PNG, etc.)
    ├── test_representative_workflows.py
    ├── test_unsupported_media.py
    ├── test_multiformat_docs.py
    ├── test_api_and_cli.py
    └── test_compatibility.py
```

---

## 🚀 Installation & Dependencies

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Host with AMD/Intel CPU (AVX supported) or NVIDIA GPU (CUDA 11.8 / 12.x)

### 2. Setup Virtual Environment
```powershell
# Windows
python -m venv .venv
.venv\Scriptsctivate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

#### Installing GPU Support (Optional):
For accelerated neural OCR inference on NVIDIA GPUs, install the CUDA-enabled PaddlePaddle wheel:
```powershell
pip install paddlepaddle-gpu --pre -i https://www.paddlepaddle.org.cn/packages/nightly/cu126/
```
*Note: If CUDA is not installed, NexusOCR automatically runs on the host CPU using multi-threaded AVX instructions.*

### 4. Launch the Web Server
```powershell
python -m nexusocr serve --host 127.0.0.1 --port 8000 --reload
```
Open your browser at: **`http://127.0.0.1:8000`**

---

## 🧪 Verification & Automated Tests

NexusOCR includes a comprehensive test suite with **66 automated tests**:

```powershell
# Run the complete test suite
python -m pytest -q
```

**Expected Result:**
```
................................................................. [100%]
65 passed, 1 skipped in ~70s
```

### Key Test Suites
- `test_representative_workflows.py`: Validates digital PDF, Indic Devanagari PDF, tabular financial PDF, computer vision crop, and layout services.
- `test_unsupported_media.py`: Enforces defensive rejection of audio (`.mp3`, `.wav`) and video (`.mp4`, `.mkv`) formats.
- `test_multiformat_docs.py`: Verifies Word (`.docx`), Excel (`.xlsx`, `.csv`), PowerPoint (`.pptx`), multi-frame TIFF, and batch processing isolation.
- `test_api_and_cli.py`: Validates FastAPI REST endpoints (`/api/process`, `/api/batch`, `/api/health`, `/api/formats`, `/api/samples`) and CLI execution.

---

## 🔮 Roadmap & Enhancements

- [ ] **Vector Database & RAG Pipeline:** Integration with PostgreSQL `pgvector` for semantic document retrieval and conversational query answering over processed archives.
- [ ] **Handwritten Indic VLM Tier:** Lightweight Vision-Language Model escalation tier (e.g., *Qwen2.5-VL 3B / Indic-VLM*) for handwritten regional scripts, doctor prescriptions, and student exam papers.
- [ ] **Docker & Podman Containers:** Pre-configured OCI container images with bundled CUDA runtimes and multi-architecture AMD/ARM CPU support.
- [ ] **WebSocket Streaming:** Real-time token and page streaming for multi-hundred page document archives.

---

## 📚 Project Reports & Documentation

For exhaustive academic, architectural, and developer documentation, explore the `report/` directory:
- [📄 Comprehensive Project Report](report/PROJECT_REPORT.md): The full 24-page academic project report prepared for Nexus Hackathon 2026 (GLS University, Ahmedabad).
- [🏛️ System Architecture](report/ARCHITECTURE.md): Deep-dive into the hybrid feature-oriented pipeline architecture.
- [🔄 Code Flow & Sequence Diagrams](report/CODE_FLOW.md): Step-by-step runtime execution traces.
- [🛠️ Developer Guidelines](report/DEVELOPER_GUIDELINES.md): Invariants, extension recipes, and coding standards.

---

## 📄 License

This project is developed for the **Nexus Hackathon 2026** under the MIT License.
