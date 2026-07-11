from __future__ import annotations

import re
from pathlib import Path

from softone_pilot.models import InvoiceData
from softone_pilot.parsers.base import (
    PdfParseError,
    SupplierParser,
    first_match,
    parse_amount,
    parse_date,
)

MONTHS_GENITIVE = {
    1: "ΙΑΝΟΥΑΡΙΟΥ",
    2: "ΦΕΒΡΟΥΑΡΙΟΥ",
    3: "ΜΑΡΤΙΟΥ",
    4: "ΑΠΡΙΛΙΟΥ",
    5: "ΜΑΙΟΥ",
    6: "ΙΟΥΝΙΟΥ",
    7: "ΙΟΥΛΙΟΥ",
    8: "ΑΥΓΟΥΣΤΟΥ",
    9: "ΣΕΠΤΕΜΒΡΙΟΥ",
    10: "ΟΚΤΩΒΡΙΟΥ",
    11: "ΝΟΕΜΒΡΙΟΥ",
    12: "ΔΕΚΕΜΒΡΙΟΥ",
}


class EgnatiaOdosParser(SupplierParser):
    vat = "802408691"
    name = "ΕΓΝΑΤΙΑ ΟΔΟΣ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ"

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if self.vat not in text and f"EL{self.vat}" not in text:
            raise PdfParseError(f"Δεν βρέθηκε το ΑΦΜ ΕΓΝΑΤΙΑ ΟΔΟΣ {self.vat}")

        number = first_match(text, (r"\bINV\s+(\d+)\b", r"\bΑΡΙΘΜΟΣ\s+(\d+)\b"))
        date_text = first_match(
            text,
            (
                r"\b(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}:\d{2}\b",
                r"ΗΜΕΡΟΜΗΝΙΑ\s+(\d{1,2}/\d{1,2}/\d{4})",
                r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
            ),
        )

        totals_line = next((line for line in text.splitlines() if "ΣΥΝΟΛΑ" in line), "")
        amounts = re.findall(r"\d+[,.]\d{2}", totals_line)
        total_text = first_match(
            text,
            (
                r"ΓΕΝΙΚΟ\s+ΣΥΝΟΛΟ\s*:\s*(?:EUR)?\s*([\d.,]+)",
                r"ΠΛΗΡΩΤΕΟ\s*:?\s*(?:EUR)?\s*([\d.,]+)",
            ),
        )
        if not number or not date_text or len(amounts) < 2 or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα ΕΓΝΑΤΙΑ ΟΔΟΣ")

        net = parse_amount(amounts[0])
        vat = parse_amount(amounts[1])
        total = parse_amount(total_text)
        self.validate_total(net, vat, total)
        invoice_date = parse_date(date_text)

        month = invoice_date.month - 1
        year = invoice_date.year
        if month == 0:
            month = 12
            year -= 1

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=f"INV-{number}",
            document_date=invoice_date,
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"ΔΙΟΔΙΑ {MONTHS_GENITIVE[month]} {year}",
            raw_text=text,
        )
