from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, parse_amount, parse_date

HEAD_RE = re.compile(
    r"^ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ\n[Α-ΩA-Z]{1,3}\n(?P<number>\d{4,})\n"
    r"(?P<date>\d{2}/\d{2}/\d{4})$",
    re.M,
)
# VAT analysis row: «24» + net glued, then VAT: "2425,00 6,00"
VAT_ROW_RE = re.compile(
    r"^(?P<pct>24|13|6)(?P<net>\d{1,3}(?:\.\d{3})*,\d{2}) (?P<vat>\d{1,3}(?:\.\d{3})*,\d{2})$", re.M
)
DESC_RE = re.compile(r"\d,\d{2}(?P<desc>ΥΠΗΡΕΣΙΕΣ ΔΙΑΔΙΚΤΥΟΥ.*?)\n(?P<more>[^\n\d][^\n]*)?\n")


class JobfindParser(SupplierParser):
    """ΒΑΔΑΣΗΣ Α. - ΠΑΤΟΥΧΑΣ Λ. ΟΕ (jobfind.gr) — job ads, ΤΠΥ series Γ, single 24% line."""

    vat = "997807550"
    name = "ΒΑΔΑΣΗΣ Α. - ΠΑΤΟΥΧΑΣ Λ. ΟΕ"

    def matches(self, normalized_text: str) -> bool:
        return f"ΑΦΜ:{self.vat}" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if "ΠΙΣΤΩΤΙΚΟ" in text:
            raise PdfParseError("Πιστωτικό JOBFIND — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        rows = list(VAT_ROW_RE.finditer(text))
        if not head or len(rows) != 1:
            raise PdfParseError(
                "Λείπουν αριθμός/ημερομηνία ή ανάλυση ΦΠΑ JOBFIND (ή πολλοί συντελεστές)"
            )
        net, vat = parse_amount(rows[0]["net"]), parse_amount(rows[0]["vat"])
        total = net + vat
        if not re.search(rf"^{re.escape(f'{total:.2f}'.replace('.', ','))}$", text, re.M):
            raise PdfParseError(f"Δεν βρέθηκε σύνολο {total:.2f} JOBFIND")
        pct = Decimal(rows[0]["pct"])
        if abs(net * pct / 100 - vat) > Decimal("0.02"):
            raise PdfParseError(f"ΦΠΑ JOBFIND {vat:.2f} != {pct}% x {net:.2f}")
        desc_match = DESC_RE.search(text)
        description = "ΥΠΗΡΕΣΙΕΣ ΔΙΑΔΙΚΤΥΟΥ JOBFIND"
        if desc_match:
            description = " ".join(filter(None, (desc_match["desc"], desc_match["more"]))).strip()
        line = InvoiceLine(
            code=head["number"],
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
            document_number=head["number"],
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=description,
            raw_text=text,
            vat_pct=pct,
            lines=(line,),
        )
