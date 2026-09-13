"""
NexusOCR Key-Value & Form Information Extractor.
Extracts structured field-value pairs, dates, amounts, and identifiers from document text.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class FormDataExtractor:
    """Extracts machine-readable form fields and key-value pairs from text and markdown."""

    # Common key-value pattern: e.g. "Invoice Number: INV-1234", "Date: 12/04/2026"
    KV_PATTERN = re.compile(
        r"^(?P<key>[A-Za-z0-9\s#\.\-_/]{2,40})\s*:\s*(?P<val>.+)$",
        re.MULTILINE
    )

    # Identifiers, amounts, dates
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    CURRENCY_PATTERN = re.compile(r"(?:[\$€£₹]|Rs\.?|USD)\s*[\d,]+(?:\.\d{2})?")
    DATE_PATTERN = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b")

    @classmethod
    def extract_form_data(cls, text: str) -> Dict[str, Any]:
        """
        Parses document text into key-value pairs and entity collections.
        """
        if not text:
            return {"key_value_pairs": {}, "entities": {}}

        key_value_pairs: Dict[str, str] = {}
        for match in cls.KV_PATTERN.finditer(text):
            k = match.group("key").strip()
            v = match.group("val").strip()
            if k and v and len(k) < 35 and "\n" not in k:
                # Avoid matching whole markdown lines like "Note: ..." if too long
                key_value_pairs[k] = v

        currencies = cls.CURRENCY_PATTERN.findall(text)
        dates = cls.DATE_PATTERN.findall(text)
        emails = cls.EMAIL_PATTERN.findall(text)
        phones = cls.PHONE_PATTERN.findall(text)

        return {
            "key_value_pairs": key_value_pairs,
            "entities": {
                "currencies": currencies,
                "dates": dates,
                "emails": emails,
                "phones": phones,
            }
        }
