"""
NexusOCR Text and Markup Processors.
Extracts structured text and tables from plain text (.txt), Markdown (.md), HTML (.html/.htm), and EPUB (.epub).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import fitz


class TextMarkupProcessor:
    """Extracts content from plain text, Markdown, HTML, XML, and EPUB files."""

    @staticmethod
    def extract_plain_text(file_path: str) -> Dict[str, Any]:
        """Reads plain text file with UTF-8 fallback."""
        try:
            content = Path(file_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = Path(file_path).read_text(encoding="latin-1", errors="replace")

        return {
            "markdown": content,
            "total_characters": len(content),
            "total_lines": len(content.splitlines()),
        }

    @staticmethod
    def extract_html(file_path: str) -> Dict[str, Any]:
        """Parses HTML/XML files into structured Markdown and extracted tables."""
        from bs4 import BeautifulSoup

        try:
            raw_html = Path(file_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_html = Path(file_path).read_text(encoding="latin-1", errors="replace")

        soup = BeautifulSoup(raw_html, "html.parser")

        # Remove scripts and styles
        for s in soup(["script", "style"]):
            s.decompose()

        tables_data: List[Dict[str, Any]] = []
        for idx, table in enumerate(soup.find_all("table")):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True).replace("\n", " ") for td in tr.find_all(["th", "td"])]
                if any(cells):
                    rows.append(cells)

            if rows:
                header = rows[0]
                body = rows[1:]
                header_line = "| " + " | ".join(header) + " |"
                sep_line = "| " + " | ".join(["---"] * max(1, len(header))) + " |"
                row_lines = ["| " + " | ".join(r) + " |" for r in body]
                md_tab = "\n".join([header_line, sep_line] + row_lines)

                tables_data.append({
                    "id": f"html_table_{idx+1}",
                    "markdown": md_tab,
                    "num_rows": len(rows),
                    "num_cols": len(header),
                })
                # Replace table tag with markdown placeholder
                table.replace_with(f"\n\n{md_tab}\n\n")

        clean_text = soup.get_text(separator="\n", strip=True)
        return {
            "markdown": clean_text,
            "title": soup.title.string if soup.title else "",
            "tables": tables_data,
        }

    @staticmethod
    def extract_epub(file_path: str) -> Dict[str, Any]:
        """Extracts text and chapter structure from EPUB documents via PyMuPDF."""
        doc = fitz.open(file_path)
        chapters: List[str] = []

        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text").strip()
                if text:
                    chapters.append(f"## Page / Section {page_idx + 1}\n\n{text}")
        finally:
            doc.close()

        full_md = "\n\n---\n\n".join(chapters) if chapters else "*(Empty EPUB)*"
        return {
            "markdown": full_md,
            "total_pages": len(doc),
        }
