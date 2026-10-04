from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import (
    PdfParseError,
    SupplierParser,
    greek_upper,
    parse_amount,
    parse_date,
)

HEAD_RE = re.compile(
    r"ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ/INVOICE\s+(?P<number>\d+)\s+(?P<date>\d{2}/\d{2}/\d{4})"
)
# "ΕΡΓΑΤΙΚΑ ΛΙΜΕΝΟΣ FREE OUT60-19 268,98 268,98 24 333,54 EUR"
# "CISF-EX WORKS10207-0 236,62 213,56 0 213,56 USD"  (unit in USD, net/total in EUR)
CHARGE_RE = re.compile(
    r"^(?P<desc>[^\n]*?[^\d\n])(?P<code>\d+-\d+) (?P<unit>[\d.]+,\d{2}) (?P<net>[\d.]+,\d{2}) "
    r"(?P<vat>\d{1,2}) (?P<total>[\d.]+,\d{2}) (?P<currency>EUR|USD)$",
    re.MULTILINE,
)
VAT_TOTAL_RE = re.compile(r"^(?P<vat>[\d.]+,\d{2})\nΣΥΝΟΛΑ$", re.MULTILINE)
# the payable amount is the last figure before the 15-digit myDATA mark
GRAND_TOTAL_RE = re.compile(r"^(?P<total>[\d.]+,\d{2})\n\d{15}\s*$", re.MULTILINE)
SHIPPER_RE = re.compile(r"\n(?P<shipper>[^\n]+)\n\d{2}/\d{2}/\d{4}\nE-Mail")


class CargoBookParser(SupplierParser):
    """ΚΑΡΓΚΟ ΜΠΟΥΚ ΝΑΥΤΙΛΙΑΚΗ ΜΕΤΑΦΟΡΙΚΗ Α.Ε. (CARGO BOOK) sea-freight forwarder invoice.

    Port/agency charges carry 24% VAT; the ocean freight lines are USD, VAT-exempt (άρθρο 27
    Ν.5144/24) and already converted to EUR in the net column. Each line keeps its own VAT and its
    CARGO BOOK charge code (``60-19``, ``10207-0``...) as category, so ``line_codes`` maps every
    charge to its own expense account (the ``-19`` suffix is 24%, ``-0`` is exempt)."""

    vat = "094475355"
    name = "ΚΑΡΓΚΟ ΜΠΟΥΚ ΝΑΥΤΙΛΙΑΚΗ ΜΕΤΑΦΟΡΙΚΗ Α.Ε."

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if re.search(r"ΠΙΣΤΩΤΙΚΟ ΤΙΜΟΛΟΓΙΟ|CREDIT NOTE", text):
            raise PdfParseError("Πιστωτικό CARGO BOOK — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        vat_match = VAT_TOTAL_RE.search(text)
        total_match = GRAND_TOTAL_RE.search(text)
        if not head or not vat_match or not total_match:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα CARGO BOOK")
        vat = parse_amount(vat_match["vat"])
        total = parse_amount(total_match["total"])

        shipper_match = SHIPPER_RE.search(text)
        shipper = greek_upper(shipper_match["shipper"]) if shipper_match else ""

        lines: list[InvoiceLine] = []
        for match in CHARGE_RE.finditer(text):
            net = parse_amount(match["net"])
            line_total = parse_amount(match["total"])
            pct = Decimal(match["vat"])
            if abs(net * pct / 100 - (line_total - net)) > Decimal("0.02"):
                raise PdfParseError(f"Γραμμή CARGO BOOK με ασύμφωνο ΦΠΑ: {match.group(0)}")
            desc = greek_upper(match["desc"])
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=f"{desc} {shipper}".strip(),
                    quantity=Decimal("1"),
                    unit_price=net,
                    discount_pct=Decimal("0"),
                    value=net,
                    vat_pct=pct,
                    category=match["code"],
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές χρεώσεων CARGO BOOK")

        net = sum((line.value for line in lines), Decimal("0"))
        lines_vat = sum(
            ((line.value * line.vat_pct / 100).quantize(Decimal("0.01")) for line in lines),
            Decimal("0"),
        )
        if abs(lines_vat - vat) > Decimal("0.02"):
            raise PdfParseError(f"ΦΠΑ γραμμών {lines_vat:.2f} != ΦΠΑ τιμολογίου {vat:.2f}")
        self.validate_total(net, vat, total)

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=head["number"],
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"ΔΙΑΜΕΤΑΦΟΡΑ {shipper}".strip(),
            raw_text=text,
            vat_pct=lines[0].vat_pct,
            lines=tuple(lines),
        )
