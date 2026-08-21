"""
Unit tests for Reading Order (RXY-Cut) and Spatial Key-Value Extraction.
"""

from core.types import ExtractedRegion, BoundingBox, ScriptType, TextType, EngineType
from core.structure_builder import sort_reading_order_rxy_cut, extract_spatial_fields


def test_reading_order_sorting():
    r1 = ExtractedRegion(
        id="1",
        bbox=BoundingBox(xmin=50, ymin=100, xmax=200, ymax=120),
        text="Line 2",
        raw_confidence=1.0,
        composite_confidence=1.0
    )
    r2 = ExtractedRegion(
        id="2",
        bbox=BoundingBox(xmin=50, ymin=50, xmax=200, ymax=70),
        text="Line 1",
        raw_confidence=1.0,
        composite_confidence=1.0
    )

    sorted_res = sort_reading_order_rxy_cut([r1, r2])
    assert sorted_res[0].id == "2"
    assert sorted_res[1].id == "1"


def test_spatial_field_extraction():
    label = ExtractedRegion(
        id="lbl",
        bbox=BoundingBox(xmin=50, ymin=50, xmax=120, ymax=70),
        text="Invoice Date:",
        raw_confidence=1.0,
        composite_confidence=1.0
    )
    value = ExtractedRegion(
        id="val",
        bbox=BoundingBox(xmin=130, ymin=50, xmax=220, ymax=70),
        text="21/08/2026",
        raw_confidence=1.0,
        composite_confidence=1.0
    )

    fields = extract_spatial_fields([label, value], schema_keys=["invoice", "date"])
    assert "date" in fields
    assert fields["date"] == "21/08/2026"
