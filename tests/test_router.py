"""
Unit tests for Difficulty Router and grouped batching.
"""

import numpy as np
import pytest
from core.difficulty_router import DifficultyRouter
from core.types import BoundingBox, ScriptType, TextType


def test_grouped_batching_empty():
    router = DifficultyRouter()
    batches = router.build_grouped_batches([])
    assert batches["latin"] == []
    assert batches["devanagari"] == []
    assert batches["gujarati"] == []
    assert batches["handwriting"] == []


def test_grouped_batching_items():
    router = DifficultyRouter()
    dummy_crop = np.zeros((30, 150, 3), dtype=np.uint8)
    dummy_bbox = BoundingBox(xmin=10, ymin=10, xmax=160, ymax=40)

    items = [(dummy_bbox, dummy_crop)]
    batches = router.build_grouped_batches(items)

    assert len(batches["latin"]) == 1
    assert batches["latin"][0][0] == 0  # Preserved index
