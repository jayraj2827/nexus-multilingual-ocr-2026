"""
NexusOCR Stage Execution and Lifecycle Controller.
Handles stage execution bounds, timing measurement, and exception handling.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from nexusocr.contracts.input import StageResult, StageStatus
from nexusocr.exceptions import StageExecutionError
from nexusocr.logging import logger
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.stage import PipelineStage


class StageExecutor:
    """Executes a single pipeline stage within a protected runtime boundary."""

    @staticmethod
    def execute_stage(stage: PipelineStage, context: ProcessingContext) -> StageResult:
        if context.is_cancelled:
            result = StageResult(
                stage_name=stage.name,
                status=StageStatus.SKIPPED,
                execution_time_ms=0.0,
                output=None,
                error="Cancelled prior to execution",
            )
            context.record_stage_result(result)
            return result

        if not stage.can_handle(context):
            result = StageResult(
                stage_name=stage.name,
                status=StageStatus.SKIPPED,
                execution_time_ms=0.0,
                output=None,
                error=None,
            )
            context.record_stage_result(result)
            return result

        start_time = time.perf_counter()
        result = StageResult(stage_name=stage.name, status=StageStatus.RUNNING)

        try:
            stage.initialize()
            output = stage.process(context)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result.status = StageStatus.COMPLETED
            result.execution_time_ms = elapsed_ms
            result.output = output
            context.record_stage_result(result)
            return result

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"{type(exc).__name__}: {str(exc)}"
            logger.warning(f"Stage '{stage.name}' execution failed: {error_msg}")

            result.status = StageStatus.FAILED
            result.execution_time_ms = elapsed_ms
            result.error = error_msg
            context.record_stage_result(result)
            raise StageExecutionError(stage.name, str(exc), original_exception=exc) from exc

        finally:
            try:
                stage.cleanup(context)
            except Exception as cleanup_err:
                logger.warning(f"Stage '{stage.name}' cleanup warning: {cleanup_err}")
