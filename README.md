# NexusOCR: Adaptive Multilingual Document Intelligence Engine

> **CPU-First & VLM-Free by Default ($>98\%$ of workloads), with selective VLM fallback for exceptional handwritten and unresolvable regions.**

NexusOCR is a high-performance document extraction engine designed to reliably extract text, complex tables, reading order, and structured key-value entities from heterogeneous PDFs (English, Hindi, Gujarati, scanned, and mixed-mode) on standard CPU hardware (**4 vCPU / 8 GB RAM**, 0 GPU).

---

## 1. System Architecture

```
                         [ MULTI-PAGE PDF ]
                                │
                                ▼
                       STAGE 1: PROFILING
                     (PyMuPDF Trust Scorer)
                                │
                 ┌──────────────┴──────────────┐
                 │ (Score >= 0.90)             │ (Score < 0.90)
                 ▼                             ▼
       [ Native Text Extraction ]    STAGE 2: ADAPTIVE RASTER
        (Fast Sub-10ms bypass)         (200 DPI base / Zoom)
                 │                             │
                 │                             ▼
                 │                   STAGE 3: LAYOUT LADDER
                 │                   (PP-DocLayout-S ──► PP-DocLayout-M)
                 │                             │
                 │                             ▼
                 │                   STAGE 4: DETECTION
                 │                   (PP-OCRv5 DBNet Detector)
                 │                             │
                 │                             ▼
                 │                   STAGE 5: ROUTING & BATCHING
                 │                   (Dominant check + Script dispatch)
                 │                             │
                 │              ┌──────────────┼──────────────┐
                 │              ▼              ▼              ▼
                 │        Printed Latin   Printed Indic  Handwriting
                 │          (PP-OCRv6)     (PP-OCRv5)     (PP-OCRv5 HW)
                 │              │              │              │
                 │              └──────────────┼──────────────┘
                 │                             ▼
                 │                   STAGE 6: MULTI-SIGNAL CONFIDENCE
                 │                             │
                 │              ┌──────────────┴──────────────┐
                 │              │ (High)                      │ (Low / Failed)
                 │              ▼                             ▼
                 │          [ Accept ]              [ DUAL-TIER FALLBACK ]
                 │              │                   ├── Fallback A: OpenCV Retry
                 │              │                   └── Fallback B: PaddleOCR-VL-1.6
                 │              │                                  (Terminal VLM)
                 │              └──────────────┬───────────────────┘
                 │                             │
                 │                             ▼
                 │                   STAGE 7: STRUCTURE & TABLES
                 │                   ├── Tables: PicoDet + SLANet
                 │                   ├── Reading Order: Recursive XY-Cut
                 │                   └── Fields: Spatial Anchors + Pydantic Schema
                 │                             │
                 └─────────────────────────────┼──────────────────────────────┐
                                               ▼                              ▼
                                     [ Structured JSON ]             [ Clean Markdown ]
                                     (+ Provenance Logs)             (+ Formatted Tables)
```

---

## 2. Model Zoo Specifications ($< 75\text{ MB}$ Total Local Footprint)

| Model Name & Version | Size | Framework | Purpose |
| :--- | :--- | :--- | :--- |
| **`PP-OCRv5_mobile_det`** | **4.7 MB** | Paddle / ONNX | Language-agnostic text line boundary detection (DBNet) |
| **`PP-OCRv6_tiny_rec` / `small_rec`** | **4.4 – 20.4 MB** | Paddle / OpenVINO | High-speed English & Latin text recognition |
| **`devanagari_PP-OCRv5_mobile_rec`**| **7.5 MB** | Paddle / ONNX | Hindi, Marathi, Nepali, Sanskrit script |
| **`Tesseract 5 LSTM (guj_best)`** | **~15.0 MB** | Tesseract C++ | Single line-crop recognizer for Gujarati (`--psm 7`) |
| **`ch_PP-OCRv5_mobile_rec` (HW)** | **~10.0 MB** | Paddle / ONNX | Fast local handwriting recognition |
| **`PP-DocLayout-S` / `M`** | **4.8 / 22.6 MB**| Paddle / PicoDet | Bounding-box layout parser (Text, Table, Title, Header) |
| **`PicoDet_layout_table`** | **7.4 MB** | Paddle / PicoDet | Table boundary detector |
| **`SLANet` / `SLANet+`** | **~10.0 MB** | Paddle / SLANet | HTML `<table>` cell structure recognizer |
| **`PaddleOCR-VL-1.6` (Decoupled)** | Remote Service | vLLM / FastAPI | Terminal VLM exception handler for unresolved handwriting |

---

## 3. Quickstart & Installation

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate  # On Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch interactive web UI (FastAPI + HTML/CSS/JS)
python app.py
```

---

## 4. Repository Structure

```
NexusOCR/
├── .venv/                      # Python virtual environment
├── data/
│   ├── models/                 # Cached model weight files
│   └── benchmark_suite/        # Ground-truth test corpus
├── core/
│   ├── types.py                # Pydantic schemas (BoundingBox, PageResult)
│   ├── profiler.py             # PyMuPDF text-layer validator & trust scorer
│   ├── preprocessor.py         # OpenCV deskew, contrast, Sauvola filter
│   ├── detector.py             # DBNet text detector wrapper
│   ├── difficulty_router.py    # Script & Text-Type Classifier
│   ├── recognizers/            # Pluggable modular OCR engines
│   ├── confidence.py           # Multi-Signal Confidence Calculator
│   ├── retry.py                # Fallback A (Crop-level OpenCV retry)
│   ├── layout.py               # PP-DocLayout-S/M layout parser
│   ├── table_engine.py         # PicoDet + SLANet table parser
│   └── structure_builder.py    # Recursive XY-Cut & JSON/MD serialization
├── frontend/                   # Web Interface (HTML5, CSS3, Modern Vanilla JS)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── benchmark/                  # Benchmark suite & evaluation harness
├── tests/                      # Unit test suite
├── app.py                      # FastAPI server for API & Web UI
└── pipeline.py                 # Unified pipeline orchestrator
```
