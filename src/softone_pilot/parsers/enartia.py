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


class EnartiaParser(SupplierParser):
    vat = "999082935"
    name = "ENARTIA ΜΟΝΟΠΡΟΣΩΠΗ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ"

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if self.vat not in text:
            raise PdfParseError(f"Δεν βρέθηκε το ΑΦΜ ENARTIA {self.vat}")

        document_number = first_match(
            text,
            (
                r"\b(ΤΠΥ-[A-ZΑ-Ω0-9]+-\d+)\b",
                r"(?:Αριθμός|Invoice\s*(?:No|Number))\s*:?\s*([A-ZΑ-Ω0-9][\w/-]+)",
            ),
        )
        date_text = first_match(
            text,
            (
                r"Ημερομηνία\s*(?:Έκδοσης|Εκδοσης)?\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
                r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
            ),
        )
        net_text = first_match(
            text,
            (
                r"ΚΑΘΑΡΗ\s+ΑΞΙΑ\s+([0-9.,]+)",
                r"Καθαρή\s*Αξία\s*:?\s*([0-9.,]+)",
                r"(?:Net\s*(?:Value|Amount)|Subtotal)\s*:?\s*([0-9.,]+)",
            ),
        )
        vat_text = first_match(
            text,
            (
                r"ΑΞΙΑ\s+Φ\.?Π\.?Α\.?\s+([0-9.,]+)",
                r"Φ\.?Π\.?Α\.?\s*(?:24%?)?\s*:?\s*([0-9.,]+)",
                r"VAT\s*(?:24%?)?\s*:?\s*([0-9.,]+)",
            ),
        )
        total_text = first_match(
            text,
            (
                r"ΤΕΛΙΚΗ\s+ΑΞΙΑ\s+([0-9.,]+)",
                r"(?:Πληρωτέο\s*Ποσό|Σύνολο\s*Πληρωμής)\s*:?\s*€?\s*([0-9.,]+)",
                r"Total\s*(?:Amount)?\s*:?\s*€?\s*([0-9.,]+)",
            ),
        )

        missing = [
            label
            for label, value in (
                ("αριθμός", document_number),
                ("ημερομηνία", date_text),
                ("καθαρή αξία", net_text),
                ("ΦΠΑ", vat_text),
                ("σύνολο", total_text),
            )
            if not value
        ]
        if missing:
            raise PdfParseError(f"Λείπουν πεδία ENARTIA: {', '.join(missing)}")

        net = parse_amount(net_text)
        vat = parse_amount(vat_text)
        total = parse_amount(total_text)
        self.validate_total(net, vat, total)

        description_match = re.search(
            r"((?:Αγορά|Ανανέωση)\s+Πακέτου[^\n]+|Κατοχύρωση[^\n]+)",
            text,
            re.IGNORECASE,
        )
        description = (
            re.sub(r"\s{2,}.*$", "", description_match.group(1)).strip()
            if description_match
            else "Υπηρεσίες Διαδικτύου"
        )

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=document_number,
            document_date=parse_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=description,
            raw_text=text,
        )
