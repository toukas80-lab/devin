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
from softone_pilot.parsers.elta import MONTH_GENITIVE

HEAD_RE = re.compile(
    r"ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ (?P<series>[Α-Ω]+) (?P<number>\d+) (?P<date>\d{2}/\d{2}/\d{4})"
)
# "Μίσθωμα του υπ ` αριθμ . XPM8586 οχήματος από 01/10/2026 έως 31/10/2026 418,00"
RENT_RE = re.compile(
    r"Μίσθωμα του υπ\W*αριθμ\W*(?P<plate>[A-ZΑ-Ω]{3}\d{4}) οχήματος "
    r"από (?P<from>\d{2}/\d{2}/\d{4}) έως (?P<to>\d{2}/\d{2}/\d{4}) (?P<net>[\d.]+,\d{2})"
)


class SfakianakisParser(SupplierParser):
    """ΣΦΑΚΙΑΝΑΚΗΣ ΑΕΒΕ (Executive Lease) monthly vehicle-rental invoice via the Impact portal."""

    vat = "094010226"
    name = "ΣΦΑΚΙΑΝΑΚΗΣ ΑΕΒΕ"

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = re.sub(r"[ \t]+", " ", text.replace("\xa0", " "))
        if re.search(r"Πιστωτικό|ΠΙΣΤΩΤΙΚΟ", text):
            raise PdfParseError("Πιστωτικό ΣΦΑΚΙΑΝΑΚΗΣ — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        rent = RENT_RE.search(text)
        net_text = first_match(text, (r"\nΣΥΝΟΛΟ (\d[\d.]*,\d{2})\n",))
        vat_text = first_match(text, (r"Φ ?\. ?Π ?\. ?Α ?\. \d+\.\d{2}% (\d[\d.]*,\d{2})",))
        total_text = first_match(text, (r"ΣΥΝΟΛΟ (\d[\d.]*,\d{2})\s*ΠΛΗΡΩΤΕΟ",))
        if not head or not rent or not net_text or not vat_text or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία, μίσθωμα ή σύνολα ΣΦΑΚΙΑΝΑΚΗΣ")
        net, vat, total = parse_amount(net_text), parse_amount(vat_text), parse_amount(total_text)
        self.validate_total(net, vat, total)
        vat_pct = self.uniform_vat_pct(net, vat)
        if parse_amount(rent["net"]) != net:
            raise PdfParseError(f"Μίσθωμα {rent['net']} != καθαρή αξία {net:.2f} ΣΦΑΚΙΑΝΑΚΗΣ")

        period_start = parse_date(rent["from"])
        month = MONTH_GENITIVE[period_start.month - 1]
        description = f"ΜΙΣΘΩΜΑ {rent['plate']} {month} {period_start.year}"
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=f"{head['series']}{head['number']}",
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=description,
            raw_text=text,
            vat_pct=vat_pct,
        )
