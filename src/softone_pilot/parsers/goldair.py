from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import (
    PdfParseError,
    SupplierParser,
    first_match,
    greek_upper,
    parse_amount,
    parse_date,
)

HEAD_RE = re.compile(
    r"ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ\s+(?P<series>[Α-Ω]+)\s+(?P<number>\d+)\s+"
    r"(?P<date>\d{2}/\d{2}/\d{4})"
)
# "704 ΟΔΙΚΟΣ ΝΑΥΛΟΣ        24        220,00        52,80        272,80"
CHARGE_RE = re.compile(
    r"^\s*(?P<code>\d{3}) (?P<desc>\S[^\n]*?)\s{2,}(?P<vat>\d{1,2})\s+(?P<net>[\d.]+,\d{2})\s+"
    r"(?P<vatamt>[\d.]+,\d{2})\s+(?P<total>[\d.]+,\d{2})\s*$",
    re.MULTILINE,
)
GRAND_TOTAL_RE = re.compile(r"Πληρωτέα Αξία\s+EUR\s+(?P<total>[\d.]+,\d{2})")


class GoldairCargoParser(SupplierParser):
    """ΓΚΟΛΝΤΑΙΡ ΚΑΡΓΚΟ (GOLDAIR CARGO) road-freight invoice. The plain text is one glued blob, so
    the layout extraction is used; one charge line per document is the norm."""

    vat = "094240542"
    name = "ΓΚΟΛΝΤΑΙΡ ΚΑΡΓΚΟ ΕΤΑΙΡΙΑ ΔΙΕΘΝΩΝ ΜΕΤΑΦΟΡΩΝ Α.Ε."
    layout = True

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if re.search(r"ΠΙΣΤΩΤΙΚΟ|CREDIT NOTE", text):
            raise PdfParseError("Πιστωτικό GOLDAIR — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        grand = GRAND_TOTAL_RE.search(text)
        if not head or not grand:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολο GOLDAIR")
        total = parse_amount(grand["total"])

        origin = first_match(text, (r"Από\s*:\s*([A-ZΑ-Ω][A-ZΑ-Ω .-]*?)\s+την\s*:",)) or ""
        shipper = first_match(text, (r"Αποστολέας\s*:\s*(?:C/O\s+)?([^\n]+?)\s{2,}",)) or ""
        shipper = greek_upper(shipper)

        lines: list[InvoiceLine] = []
        for match in CHARGE_RE.finditer(text):
            net = parse_amount(match["net"])
            vat_amount = parse_amount(match["vatamt"])
            pct = Decimal(match["vat"])
            if abs(net * pct / 100 - vat_amount) > Decimal("0.02") or abs(
                net + vat_amount - parse_amount(match["total"])
            ) > Decimal("0.02"):
                raise PdfParseError(f"Γραμμή GOLDAIR με ασύμφωνα ποσά: {match.group(0).strip()}")
            desc = " ".join(part for part in (greek_upper(match["desc"]), origin, shipper) if part)
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=desc,
                    quantity=Decimal("1"),
                    unit_price=net,
                    discount_pct=Decimal("0"),
                    value=net,
                    vat_pct=pct,
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές χρεώσεων GOLDAIR")
        if any(line.vat_pct != lines[0].vat_pct for line in lines):
            raise PdfParseError("Μεικτός ΦΠΑ GOLDAIR — καταχώριση χειροκίνητα")

        net = sum((line.value for line in lines), Decimal("0"))
        vat = sum(
            ((line.value * line.vat_pct / 100).quantize(Decimal("0.01")) for line in lines),
            Decimal("0"),
        )
        self.validate_total(net, vat, total)

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=f"{head['series']}{head['number']}",
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=lines[0].description,
            raw_text=text,
            vat_pct=lines[0].vat_pct,
            lines=tuple(lines),
        )
