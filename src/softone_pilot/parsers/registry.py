from __future__ import annotations

from pathlib import Path

from softone_pilot.models import InvoiceData
from softone_pilot.parsers.base import PdfParseError, SupplierParser, extract_pdf_text
from softone_pilot.parsers.egnatia import EgnatiaOdosParser
from softone_pilot.parsers.enartia import EnartiaParser

PARSERS: tuple[SupplierParser, ...] = (EnartiaParser(), EgnatiaOdosParser())


def parse_pdf(path: str | Path) -> InvoiceData:
    source_path = Path(path).resolve()
    text = extract_pdf_text(source_path)
    normalized = text.replace(" ", "").upper()

    for parser in PARSERS:
        if parser.vat in normalized or f"EL{parser.vat}" in normalized:
            return parser.parse_text(source_path, text)

    supported = ", ".join(parser.vat for parser in PARSERS)
    raise PdfParseError(f"Μη υποστηριζόμενος εκδότης. Υποστηριζόμενα ΑΦΜ: {supported}")
