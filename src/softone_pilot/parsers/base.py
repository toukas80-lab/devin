from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pypdf import PdfReader

from softone_pilot.models import InvoiceData


class PdfParseError(ValueError):
    pass


def extract_pdf_text(path: Path) -> str:
    if not path.is_file():
        raise PdfParseError(f"Δεν βρέθηκε το PDF: {path}")

    try:
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise PdfParseError(f"Αποτυχία ανάγνωσης PDF: {path.name}") from exc

    if not text.strip():
        raise PdfParseError(f"Το {path.name} δεν περιέχει αναγνώσιμο κείμενο")
    return text


def parse_date(value: str) -> date:
    normalized = value.strip()
    for date_format in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue
    raise PdfParseError(f"Μη έγκυρη ημερομηνία: {value}")


def parse_amount(value: str) -> Decimal:
    normalized = re.sub(r"[€\s]", "", value.strip())
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise PdfParseError(f"Μη έγκυρο ποσό: {value}") from exc


def first_match(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


class SupplierParser(ABC):
    vat: str
    name: str

    @abstractmethod
    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        raise NotImplementedError

    def validate_total(self, net: Decimal, vat: Decimal, total: Decimal) -> None:
        if abs(net + vat - total) > Decimal("0.02"):
            raise PdfParseError(
                f"Ασυμφωνία ποσών: {net:.2f} + {vat:.2f} != {total:.2f}"
            )

    def reject_proforma(self, text: str) -> None:
        if re.search(r"pro[\s-]?forma|προ[\s-]?τιμολόγιο", text, re.IGNORECASE):
            raise PdfParseError("Το αρχείο είναι proforma")
