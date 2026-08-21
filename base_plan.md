# Baseline Technical Specification: NexusOCR

This is the permanent, frozen baseline specification for **NexusOCR**. All code developed in this repository will follow the **KISS (Keep It Simple, Stupid)** principle to ensure the codebase remains clean, readable, and developer-friendly.

---

## 1. Core Architecture (The KISS Blueprint)

Rather than building complex class hierarchies, the pipeline is structured as a direct sequence of simple, modular functions with clear inputs and outputs:

```
PDF File ──► [Profiler] ──► (Trusted Native Text) ──► Output JSON/Markdown
  │
  └──► (Scanned Page) ──► [Layout Parser] ──► [Script Router] ──► [Grouped Batch Recognizer]
                                                                          │
                                                                          ▼
Output JSON/Markdown ◄── [Structured Builder] ◄── [Retry & VLM Fallback] ◄┘
```

1. **PDF Profiler**: Quickly scans text-layer metadata using `PyMuPDF`. If trusted, text is extracted natively ($<10\text{ ms}$).
2. **Layout Parser**: Uses `PP-DocLayout-S` to split scanned pages into `Text`, `Table`, and non-text blocks.
3. **Script Router & Grouped Batching**: Detects script types (Latin, Devanagari, Gujarati) and groups line crops to run a single batched OCR call per language.
4. **Specialized OCR Recognition**: Routes English to `PP-OCRv6`, Hindi to `PP-OCRv5-Devanagari`, and Gujarati to `Tesseract`.
5. **Exception Handling & Retries**:
   - **Fallback A (Cheap)**: Local OpenCV image enhancements and OCR retry on low-confidence crops.
   - **Fallback B (Terminal Exception)**: Offloads difficult handwriting or unresolvable zones to a decoupled `PaddleOCR-VL-1.6` service.
6. **Structure Builder**: Rebuilds column reading order via Recursive XY-Cut (RXY-Cut), formats tables, and maps schemas.

---

## 2. Technology & Model Zoo Specs ($< 75\text{ MB}$ Total Local Models)

To maintain simplicity, all lightweight models run on CPU:
* **DBNet Text Detector**: `PP-OCRv5_mobile_det` ($4.7\text{ MB}$)
* **Latin Recognizer**: `PP-OCRv6_tiny_rec` ($4.4\text{ MB}$)
* **Devanagari Recognizer**: `devanagari_PP-OCRv5_mobile_rec` ($7.5\text{ MB}$)
* **Gujarati Recognizer**: `Tesseract 5 LSTM (guj_best)` ($\sim 15.0\text{ MB}$)
* **Layout Segmentation**: `PP-DocLayout-S` ($4.8\text{ MB}$)
* **Table Recognition**: `PicoDet_layout_table` ($7.4\text{ MB}$) $+$ `SLANet` ($\sim 10\text{ MB}$)
* **Terminal VLM Fallback**: `PaddleOCR-VL-1.6` (decoupled remote endpoint)

---

## 3. KISS Codebase Guidelines

To keep this developer-friendly and maintainable:
* **Function-First Design**: Prefer pure functions with type hints over deep object-oriented inheritance.
* **Explicit Configurations**: Store all model thresholds and API URLs in a flat `config.py` dictionary. No complex YAML nested parsing.
* **Readable Schemas**: Use simple, flat Pydantic schemas for data parsing and representation.
* **Direct Scripting**: Keep pipeline routing inside simple `if/else` control blocks in `pipeline.py`.

---

## 4. Phased Implementation Roadmap

* **Phase 1: Benchmark Harness & Evaluation Suite** (CER, WER, Latency, Peak RSS).
* **Phase 2: PDF Profiler & OpenCV Preprocessing**.
* **Phase 3: Text Detection, Script Routing, & Recognizers**.
* **Phase 4: Multi-Signal Confidence, Fallback A (Retry), & Fallback B (VLM Client)**.
* **Phase 5: Layout Escalation, Table Parsing, & Reading Order**.
* **Phase 6: End-to-End Pipeline & Streamlit GUI**.
