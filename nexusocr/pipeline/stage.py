"""
NexusOCR Pipeline Stage Abstract Base Class.
Defines the lifecycle hooks for all pipeline stages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from nexusocr.pipeline.context import ProcessingContext


class PipelineStage(ABC):
    """
    Abstract pipeline stage contract.
    Stages must manage their own feature logic and avoid executing external
    mechanics like runner scheduling or context ownership.
    """

    def __init__(self, name: Optional[str] = None, enabled: bool = True) -> None:
        self.name: str = name or self.__class__.__name__
        self.enabled: bool = enabled

    def initialize(self) -> None:
        """Invoked before the pipeline run starts to prepare engines or resources."""
        pass

    def can_handle(self, context: ProcessingContext) -> bool:
        """Determines if this stage is eligible to execute given the current context."""
        return self.enabled and not context.is_cancelled

    @abstractmethod
    def process(self, context: ProcessingContext) -> Any:
        """
        Executes stage-specific processing.
        Returns the stage output, which is recorded in context.
        """
        pass

    def cleanup(self, context: ProcessingContext) -> None:
        """Invoked after stage completion or on error for resource cleanup."""
        pass
