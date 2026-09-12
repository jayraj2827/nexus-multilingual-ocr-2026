"""
NexusOCR Centralized Pipeline Runner.
Orchestrates sequential or ordered stage execution, lifecycle management, and error policies.
"""

from __future__ import annotations

from typing import List, Optional

from nexusocr.contracts.input import ProcessingOptions, StageResult, StageStatus
from nexusocr.contracts.results import DocumentResult
from nexusocr.exceptions import NexusOCRError
from nexusocr.logging import logger
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.execution import StageExecutor
from nexusocr.pipeline.stage import PipelineStage


class PipelineRunner:
    """
    Central pipeline orchestrator.
    Executes an ordered series of stages without knowing the internal implementation
    details of specific OCR engines or layout parsers.
    """

    def __init__(self, stages: Optional[List[PipelineStage]] = None) -> None:
        self.stages: List[PipelineStage] = stages or []

    def add_stage(self, stage: PipelineStage) -> "PipelineRunner":
        """Appends a new stage to the runner."""
        self.stages.append(stage)
        return self

    def run(self, context: ProcessingContext) -> ProcessingContext:
        """
        Executes all registered stages sequentially on the context.
        Stops early if context is cancelled.
        """
        total_stages = len(self.stages)
        for idx, stage in enumerate(self.stages):
            if context.is_cancelled:
                logger.info(f"Pipeline cancelled before stage: {stage.name}")
                context.record_stage_result(StageResult(
                    stage_name=stage.name,
                    status=StageStatus.SKIPPED,
                    execution_time_ms=0.0,
                    error="Pipeline cancelled prior to stage",
                ))
                continue

            progress_ratio = idx / total_stages if total_stages > 0 else 0.0
            context.report_progress(stage.name, progress_ratio)

            try:
                StageExecutor.execute_stage(stage, context)
            except Exception as exc:
                context.error = str(exc)
                logger.error(f"Error encountered during stage '{stage.name}': {exc}", exc=exc)
                # Re-raise to fail fast unless caller handles
                raise

        context.report_progress("completed", 1.0)
        return context

    def run_file(
        self,
        file_path: str,
        options: Optional[ProcessingOptions] = None,
    ) -> DocumentResult:
        """
        Convenience wrapper to run a document through the configured pipeline.
        Returns the resulting DocumentResult.
        """
        context = ProcessingContext(file_path=file_path, options=options)
        self.run(context)
        if context.document_result is None:
            raise NexusOCRError(f"Pipeline executed but produced no DocumentResult for {file_path}")
        return context.document_result
