"""
NexusOCR Pipeline Execution Context.
Manages state, intermediate artifacts, cancellation flags, and timing across stages.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from nexusocr.contracts.input import ProcessingOptions, StageResult, StageStatus
from nexusocr.contracts.results import DocumentResult


class ProcessingContext:
    """
    Shared runtime context flowing through pipeline stages.
    Owns execution state without containing feature-specific OCR or layout logic.
    """

    def __init__(
        self,
        file_path: str,
        options: Optional[ProcessingOptions] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> None:
        self.file_path: str = file_path
        self.options: ProcessingOptions = options or ProcessingOptions()
        self.progress_callback: Optional[Callable[[str, float], None]] = progress_callback

        self.start_time: float = time.perf_counter()
        self.is_cancelled: bool = False
        self.error: Optional[str] = None

        # Storage for intermediate artifacts passed between stages
        self.artifacts: Dict[str, Any] = {}

        # Execution stage records
        self.stage_results: Dict[str, StageResult] = {}

        # The final unified document result
        self.document_result: Optional[DocumentResult] = None

    def cancel(self) -> None:
        """Signals cancellation to all subsequent stages."""
        self.is_cancelled = True

    def report_progress(self, stage_name: str, progress_ratio: float) -> None:
        """Notifies progress callback if registered."""
        if self.progress_callback:
            try:
                self.progress_callback(stage_name, min(1.0, max(0.0, progress_ratio)))
            except Exception:
                pass

    def record_stage_result(self, result: StageResult) -> None:
        """Stores stage execution metrics."""
        self.stage_results[result.stage_name] = result

    def get_stage_result(self, stage_name: str) -> Optional[StageResult]:
        """Retrieves result from a previously executed stage."""
        return self.stage_results.get(stage_name)

    @property
    def elapsed_ms(self) -> float:
        """Total execution time in milliseconds so far."""
        return (time.perf_counter() - self.start_time) * 1000.0
