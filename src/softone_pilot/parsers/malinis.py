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
    r"^Τιμολόγιο Παροχής Υπηρεσιών[^\n]*?\s(?P<number>\d+)\s+(?P<date>\d{1,2}/\d{1,2}/\d{4})\s*$",
    re.MULTILINE,
)
# "ΕΠ-ΤΔΒ9   Εργασίες Τήρησης ... με   200,00   200,00   24   48,00" + continuation line
LINE_RE = re.compile(
    r"^(?P<code>\S+)\s{2,}(?P<desc>\S.*?)\s{2,}(?P<net>[\d.]+,\d{2})\s+(?P<after>[\d.]+,\d{2})\s+"
    r"(?P<vat>\d{1,2})\s+(?P<vatamt>[\d.]+,\d{2})\s*\n(?P<more>\s{3,}\S[^\n]*)?",
    re.MULTILINE,
)


def total(text: str, label: str) -> Decimal:
    match = re.search(rf"{label} :\s+([\d.]+,\d{{2}})\s*$", text, re.MULTILINE)
    if not match:
        raise PdfParseError(f"Λείπει «{label}» ΜΑΛΙΝΗΣ")
    return parse_amount(match.group(1))


class MalinisParser(SupplierParser):
    """ΜΑΛΙΝΗΣ ΠΕΤΡΟΣ ΔΗΜΗΤΡΙΟΣ — accounting services (ΤΠΥ, 24%)."""

    vat = "054804818"
    name = "ΜΑΛΙΝΗΣ ΠΕΤΡΟΣ ΔΗΜΗΤΡΙΟΣ"
    layout = True

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if re.search(r"Πιστωτικό", text):
            raise PdfParseError("Πιστωτικό ΜΑΛΙΝΗΣ — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        if not head:
            raise PdfParseError("Λείπουν αριθμός ή ημερομηνία ΜΑΛΙΝΗΣ")
        net = total(text, "Αξία μετά Έκπτωσης")
        vat = total(text, "ΦΠΑ")
        gross = total(text, "Σύνολο")
        self.validate_total(net, vat, gross)

        lines: list[InvoiceLine] = []
        for match in LINE_RE.finditer(text):
            value = parse_amount(match["after"])
            pct = Decimal(match["vat"])
            if abs(value * pct / 100 - parse_amount(match["vatamt"])) > Decimal("0.02"):
                raise PdfParseError(f"Γραμμή ΜΑΛΙΝΗΣ με ασύμφωνο ΦΠΑ: {match.group(0).strip()}")
            desc = " ".join(part.strip() for part in (match["desc"], match["more"] or "") if part)
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=greek_upper(desc),
                    quantity=Decimal("1"),
                    unit_price=value,
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=pct,
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές ΜΑΛΙΝΗΣ")
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=head["number"],
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=gross,
            description=lines[0].description,
            raw_text=text,
            vat_pct=self.uniform_vat_pct(net, vat),
            lines=tuple(lines),
        )
