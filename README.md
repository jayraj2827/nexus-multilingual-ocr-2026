# ⚡ NexusOCR: Adaptive Multilingual Document Intelligence Engine

![Nexus Hackathon 2026 MVP](https://img.shields.io/badge/Nexus%20Hackathon%202026-MVP%20%7C%20RTX%204060%20CUDA-success?style=flat-square&logo=nvidia)

> **🚀 Minimum Viable Product (MVP) built for the Nexus Hackathon 2026.**
> **Fast, local, GPU-accelerated document OCR & layout analysis for complex multilingual PDFs (English, Hindi, Gujarati, and mixed-mode).**

NexusOCR is a high-performance document extraction pipeline designed to extract structured text, multi-column reading order, math formulas, and tabular data from digital and scanned documents with zero external cloud dependencies.

---

## 🏛️ System Architecture

```
                          [ MULTI-PAGE PDF ]
                                  │
                                  ▼
                         PAGE TRUST PROFILER
                        (PyMuPDF Trust Scorer)
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
       (Trust Score >= 0.85)             (Trust Score < 0.85)
                  │                               │
                  ▼                               ▼
      TIER 1: DIGITAL NATIVE            TIER 2: NEURAL VISUAL OCR
        (PyMuPDF Extractor)             (PaddleOCR v3.7 PP-OCRv6)
                  │                               │
          ⚡ Latency: <40ms/page          🚀 Latency: ~150-400ms/page
          🎯 100% Exact Text              🎯 98-99% Multilingual Text
          💾 0 MB VRAM                    💾 ~800 MB VRAM (RTX 4060)
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                         UNIFIED DOCUMENT RESULT
                  ├── Clean Formatted Markdown
                  ├── Structured JSON Schema
                  └── Visual Bounding Boxes & Confidence Scores
```

---

## 🔬 The Experimental Journey & Evolution

Through iterative profiling on our target hardware (**NVIDIA RTX 4060 8GB VRAM / Windows 11**), we tested multiple paradigms before arriving at the current production architecture:

| Approach | Result / Issue | Final Action |
|:---|:---|:---|
| **Ollama / Heavy VLMs** (Qwen 7B/14B) | High latency (10–30s/page), VRAM pressure, fragile local server daemon. | ❌ Removed |
| **GOT-OCR 2.0 (580M)** | Hardcoded CUDA calls in HF modeling, 2–3 min/page on CPU, aspect ratio tensor mismatches. | ❌ Removed |
| **IBM Docling (Default)** | Slow EasyOCR CPU execution with dataloader `pin_memory` warnings. | ❌ Bypassed for OCR |
| **RapidOCR (ONNX DirectML)** | Fast (~800ms) but limited dictionary for regional Indic scripts. | ⚠️ Replaced |
| **Tiered PyMuPDF + PaddleOCR v3.7 (CUDA GPU)** | **<40ms digital extraction, ~150–400ms neural visual OCR, 98–99% multilingual accuracy.** | ✅ **Adopted** |

---

## ✨ Key Features

- **⚡ Fast Tiered Routing:** Digital pages bypass OCR completely via PyMuPDF in **<40ms**, while scanned/raster pages route to GPU-accelerated neural OCR.
- **📄 Broad Multi-Format Support:** First-class processing for **PDF, Raster & Multi-page Images (PNG, JPG, TIFF, BMP, WebP), Office documents (DOCX, XLSX, PPTX), Data files (CSV), and Text/Markup (TXT, HTML, EPUB)**.
- **🌐 Multilingual & Script-Aware:** Robust extraction across **English, Gujarati (ગુજરાતી), Hindi (हिन्दी), and Devanagari scripts**, including complex conjunct ligatures (જોડણી).
- **🚀 CUDA GPU Acceleration:** Backed by `paddlepaddle-gpu` running on NVIDIA CUDA (RTX 4060 / Ada Lovelace architecture) for sub-second visual inference.
- **📊 Table & Form Intelligence:** Reconstructs complex tables, balance sheets, and key-value form entities (amounts, dates, invoice numbers).
- **📦 Resilient Batch Processing:** Built-in batch engine with failure isolation so that unreadable files never halt a multi-document workflow.
- **🛡️ Strict Media Rejection:** Explicitly rejects unsupported audio and video streams with descriptive feedback.
- **🖥️ Interactive UI:** Built-in dashboard with real-time document navigation, colored bounding box overlays, markdown viewer, and JSON download.
- **🔒 100% Offline & Private:** Zero external cloud API calls — runs entirely on local compute.

---

## 📁 Project Structure

```
NexusOCR/
├── app.py                      # FastAPI Web Server (Compatibility Bridge)
├── config.py                   # Configuration & Constants (Compatibility Bridge)
├── pipeline.py                 # Pipeline Orchestrator (Compatibility Bridge)
├── requirements.txt            # Python Dependency Specifications
├── pytest.ini                  # Pytest Configuration
│
├── nexusocr/                   # Core Hybrid Feature-Oriented Architecture
│   ├── pipeline/               # Centralized Pipeline Execution Runtime
│   │   ├── runner.py           # Pipeline Runner & Lifecycle Scheduler
│   │   ├── context.py          # Shared Processing Context & Cancellation
│   │   ├── stage.py            # Abstract Pipeline Stage Base
│   │   └── execution.py        # Stage Execution Boundaries & Metrics
│   │
│   ├── features/               # Modular Feature Services
│   │   ├── document_ocr/       # Multi-Format OCR & Document Intelligence
│   │   ├── layout/             # Deep Document Layout & Table Service
│   │   ├── vision/             # Computer Vision & Preview Service
│   │   ├── translation/        # Multilingual Translation Service
│   │   └── batch.py            # Isolated Multi-File Batch Processor
│   │
│   ├── engines/                # External Library Adapters
│   │   ├── ocr/                # PaddleOCR, PyMuPDF, and Docling Adapters
│   │   ├── vision/             # Vision Analyzer Adapters
│   │   └── translation/        # Script & Translation Engine Adapters
│   │
│   ├── processors/             # Low-Level Document & Image Processors
│   │   ├── pdf.py              # PDF Rasterization & Page Extraction
│   │   ├── image.py            # Image BBox Cropping, Resizing & Multi-frame TIFF
│   │   ├── office.py           # Word (DOCX), Excel (XLSX/CSV), PowerPoint (PPTX)
│   │   └── text_markup.py      # Plain Text, Markdown, HTML, XML & EPUB
│   │
│   ├── contracts/              # Strict Pydantic Data Contracts & Schemas
│   │   ├── formats.py          # Format Registry, Capabilities & Validation
│   │   ├── results.py          # PageResult, DocumentResult, BoundingBox
│   │   ├── input.py            # ProcessingOptions, DocumentInput
│   │   └── output.py           # Output Formatting Helpers
│   │
│   ├── interfaces/             # External Entry Points
│   │   ├── api/                # Modular FastAPI Application & Routes
│   │   ├── cli/                # CLI Runner (`python -m nexusocr`)
│   │   └── sdk/                # Programmatic Client (`NexusOCRClient`)
│   │
│   ├── config.py               # Central Settings & Thresholds
│   ├── logging.py              # Unified Logging & Stage Diagnostics
│   └── exceptions.py           # Standardized Exception Hierarchy
│
├── engine/                     # Backward Compatibility Layer
│   ├── types.py                # Legacy Contract Re-exports
│   ├── digital_extractor.py    # Legacy PyMuPDF Extractor Re-export
│   ├── paddle_ocr_engine.py    # Legacy PaddleOCR Engine Re-export
│   └── docling_engine.py       # Legacy Docling Engine Re-export
│
├── frontend/                   # Interactive Web Studio
│   ├── index.html              # Document Upload & Results Dashboard
│   ├── app.js                  # Multi-Format Validation & Bounding Box View
│   └── styles.css              # Modern Dark Theme UI Styles
│
└── tests/                      # Automated Regression Test Suite (58+ Tests)
    ├── fixtures/               # Sample Test Documents
    ├── test_engine.py          # Legacy Engine Unit Tests
    ├── test_compatibility.py   # 100% Import & Signature Compatibility Tests
    ├── test_pipeline_architecture.py # Central Pipeline & Stage Lifecycle Tests
    ├── test_representative_workflows.py # Document Workflow Tests
    ├── test_unsupported_media.py # Audio/Video Rejection Verification Tests
    ├── test_multiformat_docs.py # Multi-format Document & Batch Tests
    ├── test_api_and_cli.py     # FastAPI REST Endpoints & CLI Tests
    └── test_python310_compat.py # Python 3.10.11 Static AST Verification
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+
- NVIDIA GPU with CUDA drivers (e.g. RTX 30xx/40xx) or CPU fallback

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/jayraj2827/nexus-multilingual-ocr-2026.git
cd nexus-multilingual-ocr-2026

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Install CUDA-enabled PaddlePaddle (for NVIDIA GPUs)
pip install paddlepaddle-gpu --pre -i https://www.paddlepaddle.org.cn/packages/nightly/cu126/
```

### 3. Run the Application
```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
Open your browser at: **`http://127.0.0.1:8000`**

---

## 🔌 API Reference

### `POST /api/process`
Process an uploaded PDF or image file through the tiered pipeline.

**Request:** `multipart/form-data` with `file: UploadFile`

**Response (`200 OK`):**
```json
{
  "file_name": "sample.pdf",
  "total_pages": 2,
  "average_trust_score": 0.96,
  "total_execution_time_ms": 320.5,
  "full_markdown": "# Reconstructed Document Content...",
  "pages": [
    {
      "page_number": 1,
      "width": 1200,
      "height": 1600,
      "is_digital": true,
      "trust_score": 0.98,
      "markdown": "...",
      "execution_time_ms": 32.4
    }
  ]
}
```

### `GET /api/page_image/{filename}/{page_number}`
Returns the rendered PNG image of a specific page for visual bounding box inspection.

### `GET /api/health`
Returns the server status and GPU availability.

---

## 📊 Benchmark & Real-World Validation

| Test Case | Pages | Nature of Document | Total Time | Accuracy |
|:---|:---:|:---|:---:|:---:|
| **Multilingual Presentation** | 13 | Mixed Digital & Visual Infographics | **20.7s** | **99.5%** |
| **Saheb Tuition Exam Paper** | 2 | Printed Gujarati Script + Accounting Tables | **~0.8s** | **98.5%** |
| **12th Board Answersheet** | 7 | Mixed Gujarati Cursive + Math Calculations | **~3.8s** | **100% Math** |
| **Digital Attendance Report** | 1 | Digital Native Tables | **~43ms** | **100%** |
| **University Marksheet** | 2 | Dense Tabular Layout | **~113ms** | **100%** |

---

## 🧪 Running Tests

```powershell
pytest tests/test_engine.py -v
```

## 🔮 Future Roadmap & Enhancements

- **🐘 PostgreSQL & Vector Database Integration:** Integrate a robust **PostgreSQL** backend with `pgvector` for persistent document storage, extraction audit histories, and semantic document search / retrieval-augmented generation (RAG) over processed archives.
- **⚛️ Frontend Modernization (React + Vite):** Transition the client interface to a modular **React + Tailwind CSS** architecture featuring batch multi-document queues, interactive side-by-side annotation tools, and real-time WebSocket progress streaming.
- **🧠 Vision-Language Model (VLM) Escalation Tier:** Integrate a lightweight Vision-Language Model (e.g., *Qwen2.5-VL 3B / Gemma-3-VL / Indic VLM*) specifically tailored for high-accuracy recognition of **complex, cursive regional handwritten text** (such as Gujarati and Hindi student board answersheets, doctor prescriptions, and historical manuscripts).
- **📑 Deep Table Reconstruction:** Enhance cell-span and nested table recognition using dedicated layout transformers.
- **🐳 Docker Containerization:** Provide ready-to-use Docker images with pre-configured CUDA runtime drivers for one-click cross-platform deployment.
