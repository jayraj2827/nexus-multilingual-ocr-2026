"""
Structure Reconstruction, Recursive XY-Cut (RXY-Cut) Reading Order, and Schema Validation.
"""

from typing import List, Dict, Any
from core.types import ExtractedRegion, TableStructure, BoundingBox


def sort_reading_order_rxy_cut(regions: List[ExtractedRegion]) -> List[ExtractedRegion]:
    """
    Sorts bounding boxes into proper human reading order using Recursive XY-Cut heuristics.
    Decomposes multi-column layouts into left-to-right columns and top-to-bottom lines.
    """
    if not regions:
        return []

    # Simple, robust 2-pass spatial sort:
    # 1. Detect if page is multi-column by looking at horizontal midpoint split
    x_centers = [(r.bbox.xmin + r.bbox.xmax) / 2.0 for r in regions]
    min_x = min(r.bbox.xmin for r in regions)
    max_x = max(r.bbox.xmax for r in regions)
    page_width = max_x - min_x

    # If document has wide horizontal span and distinct column clusters:
    midpoint = min_x + (page_width / 2.0)
    left_col = [r for r in regions if r.bbox.xmax <= midpoint + 20]
    right_col = [r for r in regions if r.bbox.xmin >= midpoint - 20]

    # If cleanly partitioned into 2 columns (at least 70% of elements fit in columns)
    if (len(left_col) + len(right_col)) >= 0.70 * len(regions) and len(left_col) > 2 and len(right_col) > 2:
        left_col.sort(key=lambda r: r.bbox.ymin)
        right_col.sort(key=lambda r: r.bbox.ymin)
        middle_items = [r for r in regions if r not in left_col and r not in right_col]
        middle_items.sort(key=lambda r: r.bbox.ymin)
        return left_col + right_col + middle_items

    # Standard single-column / line-clustered reading order (top-to-bottom, line grouping within 10px)
    sorted_regions = sorted(regions, key=lambda r: (round(r.bbox.ymin / 12.0) * 12.0, r.bbox.xmin))
    return sorted_regions


def extract_spatial_fields(regions: List[ExtractedRegion], schema_keys: List[str] = None) -> Dict[str, Any]:
    """
    Extracts key-value fields using geometric raycasting (searching right and below a label).
    """
    if schema_keys is None:
        schema_keys = ["invoice", "date", "total", "amount", "gstin", "pan", "email", "phone"]

    extracted = {}
    for r in regions:
        text_lower = r.text.lower().strip()
        for key in schema_keys:
            if key in text_lower and len(text_lower) < 40:
                # Find nearest box immediately to the right or directly below
                val = _find_nearest_value_box(r, regions)
                if val and key not in extracted:
                    extracted[key] = val

    return extracted


def _find_nearest_value_box(label_region: ExtractedRegion, all_regions: List[ExtractedRegion]) -> str:
    """Finds the closest text box to the right or below the label."""
    l_box = label_region.bbox
    candidates = []

    for other in all_regions:
        if other.id == label_region.id:
            continue
        o_box = other.bbox

        # Check Right
        if o_box.xmin >= l_box.xmax - 5 and abs(o_box.ymin - l_box.ymin) < 15:
            dist = o_box.xmin - l_box.xmax
            candidates.append((dist, other.text))

        # Check Below
        elif o_box.ymin >= l_box.ymax - 5 and abs(o_box.xmin - l_box.xmin) < 40:
            dist = (o_box.ymin - l_box.ymax) * 1.5
            candidates.append((dist, other.text))

    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    return ""


def build_final_markdown(sorted_regions: List[ExtractedRegion], tables: List[TableStructure]) -> str:
    """Combines text blocks and tables into a clean Markdown document."""
    lines = []

    # Insert text lines
    for r in sorted_regions:
        if r.text.strip():
            lines.append(r.text.strip())

    # Append formatted tables
    if tables:
        lines.append("\n### Extracted Tables\n")
        for idx, t in enumerate(tables):
            lines.append(f"**Table {idx + 1}:**\n")
            lines.append(t.markdown)
            lines.append("")

    return "\n\n".join(lines)
