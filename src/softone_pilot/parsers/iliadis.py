from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, parse_amount, parse_date

HEAD_RE = re.compile(r"^\s*(?P<number>[HΗ]ΤΠΥ[Α-ΩA-Z]?\d+)\s+(?P<date>\d{2}/\d{2}/\d{4})\s*$", re.M)
NET_RE = re.compile(r"ΣΥΝΟΛΑ\s*:\s*[\d.]+,\d{2}\s+(?P<net>[\d.]+,\d{2})\s*$", re.M)
# gross and VAT are glued on one line: "186,0036,00"
AMOUNT = r"\d{1,3}(?:\.\d{3})*,\d{2}"
GROSS_VAT_RE = re.compile(rf"^(?P<gross>{AMOUNT})(?P<vat>{AMOUNT})$", re.M)


class IliadisCargoParser(SupplierParser):
    """ΗΛΙΑΔΗΣ ΚΑΡΓΚΟ Α.Ε. — domestic road transport (ΤΠΥ, 24%). The shipper column often names
    another supplier (e.g. ΕΛΛΗΝΙΚΑ ΝΑΥΤΙΚΑ ΠΡΑΚΤΟΡΕΙΑ with its ΑΦΜ), so this parser must be
    registered before those suppliers."""

    vat = "997996290"
    name = "ΗΛΙΑΔΗΣ ΚΑΡΓΚΟ ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ"

    def matches(self, normalized_text: str) -> bool:
        return "ΗΛΙΑΔΗΣΚΑΡΓΚΟ" in normalized_text and self.vat in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if re.search(r"Πιστωτικό", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό ΗΛΙΑΔΗΣ — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        net_match = NET_RE.search(text)
        if not head or not net_match:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή καθαρή αξία ΗΛΙΑΔΗΣ")
        net = parse_amount(net_match["net"])
        for match in GROSS_VAT_RE.finditer(text):
            gross, vat = parse_amount(match["gross"]), parse_amount(match["vat"])
            if abs(net + vat - gross) <= Decimal("0.02"):
                break
        else:
            raise PdfParseError("Λείπουν ΦΠΑ / σύνολο ΗΛΙΑΔΗΣ")
        pct = self.uniform_vat_pct(net, vat)
        number = "Η" + head["number"][1:]
        description = "ΜΕΤΑΦΟΡΙΚΑ ΗΛΙΑΔΗΣ ΚΑΡΓΚΟ"
        line = InvoiceLine(
            code=number,
            description=description,
            quantity=Decimal("1"),
            unit_price=net,
            discount_pct=Decimal("0"),
            value=net,
            vat_pct=pct,
        )
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=gross,
            description=description,
            raw_text=text,
            vat_pct=pct,
            lines=(line,),
        )
