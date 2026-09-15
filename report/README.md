# NexusOCR Technical Documentation & Engineering Reports

Welcome to the technical documentation and project report directory for **NexusOCR: Multilingual Document OCR Extraction Pipeline**, developed as part of **Nexus Hackathon 2026** (Affiliated to GLS University, Ahmedabad by Harsh Aalwani & Jayraj Prajapati).

---

## 📚 Document Index

1. **[Comprehensive Project Report (PROJECT_REPORT.md)](PROJECT_REPORT.md)**
   - Complete 24-page academic and engineering project report.
   - Includes Abstract, Problem Statement, Objectives, Operating Principle (Fig 2.6.1), Feasibility Study, Prototyping Lifecycle (Fig 4.2.1), Risk Analysis, Task Dependency, Timeline Chart, Detailed SRS, DFDs (Level 0, Level 1, Level 2), Architectural Layer Model (Fig 6.1.1), Interface Designs (6.2.1–6.2.8), Verification Test Matrix (66 tests: 65 passed, 1 skipped), Future Enhancements, and Appendices A–C.

2. **[Architecture & System Design (ARCHITECTURE.md)](ARCHITECTURE.md)**
   - High-level architectural pattern (Hybrid Feature-Oriented Pipeline).
   - Layer breakdown: `pipeline/`, `features/`, `engines/`, `processors/`, `contracts/`, and `interfaces/`.
   - Complete component topology and dependency boundaries.
   - Non-intrusive backward compatibility architecture (legacy shims & bridges).

3. **[Code Flow & Execution Tracing (CODE_FLOW.md)](CODE_FLOW.md)**
   - Complete end-to-end request lifecycles (REST API, CLI, Python SDK).
   - 2-Tier Adaptive Document Routing mechanism (PyMuPDF Tier 1 @ ~11-30ms vs PaddleOCR Tier 2 @ ~150-400ms GPU / ~1.08s CPU).
   - Central pipeline execution lifecycle (`ProcessingContext` & `PipelineStage`).
   - Multimodal workflows (PDF, Office DOCX/XLSX/PPTX, Images/TIFF, Markup, Translation).
   - Sequence diagrams illustrating runtime interactions.

4. **[Developer Guidelines & Future Roadmap (DEVELOPER_GUIDELINES.md)](DEVELOPER_GUIDELINES.md)**
   - Architectural invariants and golden rules.
   - Step-by-step recipes: Adding pipeline stages, engine adapters, and media processors.
   - Deterministic Python 3.10.11 compatibility guardrails.
   - Automated testing, logging, and error-handling standards.

---

## 🏛️ Architecture Layer Model

```
                              [ Client: Web UI / CLI / SDK ]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [ 1. Interfaces Layer ]                     [ 6. Shared Contracts ]
          (FastAPI REST, CLI, SDK)                     (Formats, Input, Result, BBox)
                       │                                           ▲
                       ▼                                           │
         [ 2. Central Pipeline Runtime ]                           │
       (PipelineRunner, Context, StageExecutor)                     │
                       │                                           │
                       ▼                                           │
             [ 3. Domain Features ] ───────────────────────────────┘
      (document_ocr, layout, vision, batch, translation)
                       │
                       ▼
        [ 4. Reusable Document Processors ]
           (pdf, image, office, text_markup)
                       │
                       ▼
             [ 5. Engine Adapters ]
     (PyMuPDF, PaddleOCR, Docling, Vision, Translation)
```

---

## 🧪 Verification Status

- **Automated Tests:** 66 tests (65 passed, 1 skipped optional GPU test).
- **Execution Time:** ~70 seconds.
- **Success Rate:** 100% across executed tests.
- **Zero-Cloud Guarantee:** 100% offline, local-first execution.
