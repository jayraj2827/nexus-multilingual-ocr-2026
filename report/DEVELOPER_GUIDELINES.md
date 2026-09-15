# NexusOCR Developer Guidelines & Engineering Invariants

**NexusOCR: Multilingual Document OCR Extraction Pipeline**  
*Adaptive Multilingual Document Intelligence Engine*  
*Nexus Hackathon 2026 (GLS University, Ahmedabad) by Harsh Aalwani & Jayraj Prajapati*

This guide establishes the engineering standards, architectural invariants, extension recipes, and compatibility rules for developers building on the **NexusOCR** codebase.

---

## 1. Core Architectural Invariants

Whenever you extend or modify the codebase, you MUST adhere to these architectural invariants:

1. **Do Not Pollute `pipeline/` with Feature Logic**:
   - `nexusocr/pipeline/` owns stage lifecycle, scheduling, progress callbacks, and cancellation.
   - Never import OCR libraries (PaddleOCR, PyMuPDF) or write business decisions inside `pipeline/`.
2. **Keep Processors Pure and Stateless**:
   - `nexusocr/processors/` handles technical I/O (reading bytes, decoding images, parsing OpenXML).
   - Processors must not make domain decisions or hold feature state.
3. **Isolate Third-Party Libraries Behind `engines/`**:
   - Every external library, neural model, or provider integration (e.g., PaddleOCR, PyMuPDF, Docling) must live inside `nexusocr/engines/` and implement an abstract base class.
4. **Never Break Existing Public Imports**:
   - Always maintain backward compatibility bridges in legacy paths (`app.py`, `pipeline.py`, `config.py`).
5. **Enforce Python 3.10.11 Compatibility**:
   - Do not use syntax or standard-library features exclusive to Python 3.11+.
6. **Preserve Zero-Cloud Local Execution**:
   - Never introduce outbound network dependencies into the core document extraction flow.

---

## 2. Step-by-Step Extension Recipes

### Recipe A: Adding a New Pipeline Stage
Subclass `PipelineStage` from `nexusocr.pipeline.stage`:
```python
from typing import Any
from nexusocr.pipeline.stage import PipelineStage
from nexusocr.pipeline.context import ProcessingContext

class CustomAnalysisStage(PipelineStage):
    def __init__(self, name: str = "CustomAnalysisStage", enabled: bool = True):
        super().__init__(name=name, enabled=enabled)

    def can_handle(self, context: ProcessingContext) -> bool:
        return super().can_handle(context) and context.document_result is not None

    def process(self, context: ProcessingContext) -> Any:
        text = context.document_result.full_markdown
        # Perform custom logic
        result = {"analysis": "complete"}
        context.artifacts["custom_analysis"] = result
        return result
```

### Recipe B: Integrating a New Vision Engine Adapter
Implement `BaseOCREngine` from `nexusocr.engines.ocr.base`:
```python
from typing import Optional
import numpy as np
from nexusocr.contracts.results import PageResult
from nexusocr.engines.ocr.base import BaseOCREngine

class CustomVisionEngine(BaseOCREngine):
    def is_available(self) -> bool:
        return True

    def process_page_image(self, page_img: np.ndarray, page_num: int) -> Optional[PageResult]:
        # Process numpy image and return PageResult
        ...
```

---

## 3. Automated Testing Standards

NexusOCR enforces a strict automated verification standard:
- **Test Runner:** `pytest`
- **Current Suite:** 66 automated tests (65 passed, 1 skipped optional GPU test).
- **Execution:**
  ```powershell
  python -m pytest -q
  ```
- Any new feature or processor must include unit tests under `tests/` verifying happy-path execution, corrupt file rejection, and defensive media handling.
