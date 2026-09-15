"""
NexusOCR Pipeline Architecture Unit Tests.
Tests runner orchestration, stage lifecycles, context sharing, and error handling.
"""

from typing import Any
import pytest

from nexusocr.contracts.input import ProcessingOptions, StageStatus
from nexusocr.exceptions import StageExecutionError
from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.execution import StageExecutor
from nexusocr.pipeline.runner import PipelineRunner
from nexusocr.pipeline.stage import PipelineStage


class MockStageA(PipelineStage):
    def __init__(self):
        super().__init__(name="StageA")
        self.initialized = False
        self.cleaned_up = False

    def initialize(self):
        self.initialized = True

    def process(self, context: ProcessingContext) -> str:
        context.artifacts["from_stage_a"] = "data_a"
        return "result_a"

    def cleanup(self, context: ProcessingContext):
        self.cleaned_up = True


class MockStageB(PipelineStage):
    def __init__(self):
        super().__init__(name="StageB")

    def process(self, context: ProcessingContext) -> str:
        prev = context.artifacts.get("from_stage_a", "")
        context.artifacts["from_stage_b"] = f"{prev}->data_b"
        return "result_b"


class MockFailingStage(PipelineStage):
    def __init__(self):
        super().__init__(name="FailingStage")

    def process(self, context: ProcessingContext) -> Any:
        raise ValueError("Simulated stage failure")


def test_processing_context_lifecycle():
    """Verifies context initialization, artifact tracking, progress reporting, and cancellation."""
    progress_records = []

    def on_progress(stage: str, ratio: float):
        progress_records.append((stage, ratio))

    ctx = ProcessingContext(
        file_path="sample.pdf",
        options=ProcessingOptions(max_pages=5),
        progress_callback=on_progress
    )

    assert ctx.file_path == "sample.pdf"
    assert ctx.options.max_pages == 5
    assert ctx.is_cancelled is False
    assert ctx.elapsed_ms >= 0.0

    ctx.report_progress("test_stage", 0.5)
    assert len(progress_records) == 1
    assert progress_records[0] == ("test_stage", 0.5)

    ctx.cancel()
    assert ctx.is_cancelled is True


def test_stage_executor_normal_flow():
    """Verifies stage lifecycle execution: initialize -> process -> cleanup."""
    stage_a = MockStageA()
    ctx = ProcessingContext("doc.pdf")

    res = StageExecutor.execute_stage(stage_a, ctx)

    assert res.status == StageStatus.COMPLETED
    assert res.output == "result_a"
    assert res.execution_time_ms >= 0.0
    assert stage_a.initialized is True
    assert stage_a.cleaned_up is True
    assert ctx.artifacts["from_stage_a"] == "data_a"


def test_stage_executor_failure_handling():
    """Verifies that stage failures are caught, recorded, and wrapped cleanly."""
    failing_stage = MockFailingStage()
    ctx = ProcessingContext("doc.pdf")

    with pytest.raises(StageExecutionError) as exc_info:
        StageExecutor.execute_stage(failing_stage, ctx)

    assert "FailingStage" in str(exc_info.value)
    recorded = ctx.get_stage_result("FailingStage")
    assert recorded is not None
    assert recorded.status == StageStatus.FAILED
    assert "ValueError: Simulated stage failure" in recorded.error


def test_pipeline_runner_orchestration():
    """Verifies PipelineRunner executes multiple stages in order and flows artifacts."""
    runner = PipelineRunner()
    stage_a = MockStageA()
    stage_b = MockStageB()
    runner.add_stage(stage_a).add_stage(stage_b)

    ctx = ProcessingContext("test.pdf")
    runner.run(ctx)

    assert ctx.artifacts["from_stage_a"] == "data_a"
    assert ctx.artifacts["from_stage_b"] == "data_a->data_b"
    assert "StageA" in ctx.stage_results
    assert "StageB" in ctx.stage_results


def test_pipeline_runner_cancellation():
    """Verifies PipelineRunner aborts gracefully when context is marked cancelled."""
    runner = PipelineRunner()
    stage_a = MockStageA()
    stage_b = MockStageB()
    runner.add_stage(stage_a).add_stage(stage_b)

    ctx = ProcessingContext("test.pdf")
    ctx.cancel()
    runner.run(ctx)

    # Stages were skipped because context was cancelled
    res_a = ctx.get_stage_result("StageA")
    assert res_a is not None
    assert res_a.status == StageStatus.SKIPPED
    assert "from_stage_a" not in ctx.artifacts
