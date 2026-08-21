"""
Table Structure Extraction using PicoDet and SLANet.
Converts table crops directly into structured HTML grids and Markdown tables.
"""

from typing import List, Optional
import numpy as np
from core.types import TableStructure, TableCell, BoundingBox


class TableEngine:
    """Detects and parses tables into structured matrices."""

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._table_engine = None

    def _lazy_init(self):
        if self._table_engine is None:
            from paddleocr import PPStructure
            # SLANet table structure parser
            self._table_engine = PPStructure(
                show_log=False,
                use_gpu=self.use_gpu,
                layout=False,
                table=True,
                ocr=True
            )

    def extract_table(self, table_crop: np.ndarray, global_bbox: BoundingBox, table_id: str) -> Optional[TableStructure]:
        """
        Parses a cropped table region and outputs a TableStructure object.
        """
        if table_crop is None or table_crop.size == 0:
            return None

        self._lazy_init()

        try:
            results = self._table_engine(table_crop)
        except Exception:
            return None

        if not results:
            return None

        res = results[0]
        html_str = res.get("res", {}).get("html", "")
        if not html_str:
            return None

        # Build clean markdown from HTML table
        markdown_str = self._html_to_markdown(html_str)
        cells = []

        # Extract cell coordinates if available
        cell_boxes = res.get("res", {}).get("cell_bbox", [])
        for idx, cb in enumerate(cell_boxes):
            c_bbox = BoundingBox(
                xmin=global_bbox.xmin + float(cb[0]),
                ymin=global_bbox.ymin + float(cb[1]),
                xmax=global_bbox.xmin + float(cb[2]),
                ymax=global_bbox.ymin + float(cb[3])
            )
            cells.append(TableCell(
                row_idx=0,
                col_idx=idx,
                text="",
                bbox=c_bbox
            ))

        return TableStructure(
            id=table_id,
            bbox=global_bbox,
            html=html_str,
            markdown=markdown_str,
            num_rows=max(1, html_str.count("<tr>")),
            num_cols=max(1, html_str.count("<td>") // max(1, html_str.count("<tr>"))),
            cells=cells
        )

    def _html_to_markdown(self, html: str) -> str:
        """Converts basic <table> HTML structure to clean GFM Markdown."""
        try:
            import re
            rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL)
            if not rows:
                return html

            md_lines = []
            header_done = False

            for r in rows:
                cols = re.findall(r'<t[dh].*?>(.*?)</t[dh]>', r, re.DOTALL)
                clean_cols = [c.strip().replace('\n', ' ') for c in cols]
                md_lines.append("| " + " | ".join(clean_cols) + " |")

                if not header_done:
                    md_lines.append("| " + " | ".join(["---"] * len(clean_cols)) + " |")
                    header_done = True

            return "\n".join(md_lines)
        except Exception:
            return html
