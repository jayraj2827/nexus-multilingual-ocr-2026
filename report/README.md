# NexusOCR Architectural Documentation & Engineering Report

Welcome to the comprehensive technical documentation for the **NexusOCR** document intelligence platform. This directory provides an architectural breakdown, execution flow traces, and forward-looking engineering guidelines.

---

## 📚 Document Index

1. **[Architecture & System Design](ARCHITECTURE.md)**
   * High-level architectural pattern (Hybrid Feature-Oriented Pipeline).
   * Layer breakdown: `pipeline/`, `features/`, `engines/`, `processors/`, `contracts/`, and `interfaces/`.
   * Complete component topology and dependency boundaries.
   * Backward compatibility architecture (legacy shims & bridges).

2. **[Code Flow & Execution Tracing](CODE_FLOW.md)**
   * Complete end-to-end request lifecycles (REST API, CLI, Python SDK).
   * 2-Tier Adaptive Document Routing mechanism (PyMuPDF Tier 1 vs PaddleOCR Tier 2 GPU).
   * Central pipeline execution lifecycle (`ProcessingContext` & `PipelineStage`).
   * Multimodal workflows (PDF, Image, Video, Audio, Translation, Layout).
   * Sequence diagrams illustrating runtime interactions.

3. **[Developer Guidelines & Future Roadmap](DEVELOPER_GUIDELINES.md)**
   * Architectural invariants and golden rules.
   * Step-by-step guide: Adding a new pipeline stage.
   * Step-by-step guide: Integrating a new engine adapter (e.g., VLM / Qwen2.5-VL).
   * Step-by-step guide: Adding a new media processor or feature service.
   * Python 3.10.11 compatibility guardrails.
   * Testing, logging, and error-handling standards.

---

## 🏛️ Quick Architecture Overview

```mermaid
graph TD
    Client["Client (Web UI / CLI / SDK)"]
    
    subgraph Interfaces ["1. Interfaces Layer (nexusocr.interfaces)"]
        API["FastAPI REST Endpoints (api/)"]
        CLI["Command-Line Interface (cli/)"]
        SDK["Python SDK (sdk/client.py)"]
    end

    subgraph PipelineRuntime ["2. Central Pipeline Runtime (nexusocr.pipeline)"]
        Runner["PipelineRunner"]
        Context["ProcessingContext"]
        StageExec["StageExecutor"]
        BaseStage["PipelineStage (Abstract)"]
    end

    subgraph Features ["3. Domain Features (nexusocr.features)"]
        OCRFeature["document_ocr/ (Multi-Format & Form Extraction)"]
        LayoutFeature["layout/ (Docling & TableFormer)"]
        VisionFeature["vision/ (Inspection & Preview)"]
        BatchFeature["batch.py (Isolated Multi-File Queue)"]
        TransFeature["translation/ (Script Detection & Translate)"]
    end

    subgraph Processors ["4. Reusable Document Processors (nexusocr.processors)"]
        ProcPDF["pdf.py (PyMuPDF I/O)"]
        ProcImg["image.py (Pillow & Multi-frame TIFF)"]
        ProcOffice["office.py (Word, Excel, PowerPoint)"]
        ProcText["text_markup.py (Text, HTML, Markdown, EPUB)"]
    end

    subgraph Engines ["5. Hardware & 3rd-Party Engine Adapters (nexusocr.engines)"]
        EngPyMu["ocr/pymupdf.py"]
        EngPaddle["ocr/paddleocr.py (RTX 4060 CUDA)"]
        EngDocling["ocr/docling.py"]
        EngVision["vision/base.py"]
        EngTrans["translation/base.py"]
    end

    subgraph Contracts ["6. Strict Shared Contracts (nexusocr.contracts)"]
        FormatContract["formats.py (FormatResolver & Capabilities)"]
        ResultsContract["results.py (DocumentResult, PageResult, BoundingBox)"]
        InputContract["input.py (ProcessingOptions, DocumentInput)"]
    end

    Client --> Interfaces
    Interfaces --> PipelineRuntime
    Interfaces --> Features
    PipelineRuntime --> Features
    Features --> Processors
    Features --> Engines
    Features --> Contracts
    PipelineRuntime --> Contracts
    Processors --> Contracts
```

---

## 🔍 Core Design Principles

1. **Strict Separation of Execution Mechanics vs Domain Decisions**:
   - `pipeline/` manages *how* stages execute (timing, cancellation, progress, errors).
   - `features/` manages *what* business logic is performed (trust scoring, tier selection, translation).
2. **Hardware & Provider Isolation**:
   - Heavy dependencies (PaddleOCR, CUDA, Docling, PyMuPDF) live strictly inside `engines/`.
   - The rest of the codebase interacts via abstract base classes and typed contracts.
3. **Zero Breaking Changes via Non-Intrusive Bridges**:
   - The project preserves all legacy import paths (`from pipeline import NexusOCRPipeline`, `from engine.types import ...`, `import config`, `from app import app`) through lightweight compatibility shims.
4. **Deterministic Python 3.10.11 Compatibility**:
   - Verified via AST parsing to prevent any Python 3.11+ syntax or standard library leakage.
