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

# Entersoft layout "ΤΙΜΟΛΟΓΙΟ ΠΩΛΗΣΗΣ - ΔΕΛΤΙΟ ΑΠΟΣΤΟΛΗΣ", series+number "Β 1838".
# The issuer name/AFM is only in the header image, so detection uses the site URL.
# Items carry no supplier code (column shows "0"): the SoftOne item is resolved from
# the normalized description through the supplier `item_map`.

LINE_RE = re.compile(
    r"^\s*\d+\s+(?P<desc>\S.*?)\s{2,}(?P<unit>\S+)\s+"
    r"(?P<qty>[\d.]+,\d{2})\s+(?P<price>[\d.]+,\d{2,4})\s+(?P<value>[\d.]+,\d{2})\s*$"
)
TABLE_END_RE = re.compile(r"ΠΛΗΘΟΣ ΣΥΣΚΕΥΑΣΙΩΝ|^\s*ΑΞΙΑ\s+% ΦΠΑ", re.MULTILINE)


class PrometalParser(SupplierParser):
    """ΠΡΟΜΕΤΑΛ ΜΠΑΚΛΗ ΑΕΒΕ (purchase of goods, no supplier item codes)."""

    vat = "094012139"
    name = "ΠΡΟΜΕΤΑΛ ΜΠΑΚΛΗ ΑΕΒΕ"
    layout = True

    def matches(self, normalized_text: str) -> bool:
        return "PROMETALBAKLI.GR" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if re.search(r"ΠΙΣΤΩΤΙΚΟ", text):
            raise PdfParseError("Πιστωτικό ΠΡΟΜΕΤΑΛ — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        if not re.search(r"ΤΙΜΟΛΟΓΙΟ ΠΩΛΗΣΗΣ\s*-\s*ΔΕΛΤΙΟ ΑΠΟΣΤΟΛΗΣ", text):
            raise PdfParseError("Άγνωστος τύπος παραστατικού ΠΡΟΜΕΤΑΛ (όχι ΤΠ-ΔΑ)")

        number_match = re.search(r"ΣΕΙΡΑ - ΑΡΙΘΜΟΣ\s+(?P<series>\S+)\s+(?P<number>\d+)", text)
        date_text = first_match(text, (r"ΗΜΕΡΟΜΗΝΙΑ\s+(\d{2}/\d{2}/\d{4})",))
        net_text = first_match(text, (r"ΚΑΘΑΡΗ ΑΞΙΑ[ \t]+([\d.]+,\d{2})",))
        vat_text = first_match(text, (r"ΣΥΝΟΛΟ ΦΠΑ[ \t]+([\d.]+,\d{2})",))
        total_text = first_match(text, (r"ΤΕΛΙΚΗ ΑΞΙΑ \(€\)[ \t]+([\d.]+,\d{2})",))
        if not number_match or not date_text or not net_text or not vat_text or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα ΠΡΟΜΕΤΑΛ")

        net = parse_amount(net_text)
        vat = parse_amount(vat_text)
        total = parse_amount(total_text)
        self.validate_total(net, vat, total)
        vat_pct = self.uniform_vat_pct(net, vat)

        lines = self._parse_lines(text, vat_pct)
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές ειδών ΠΡΟΜΕΤΑΛ")
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        series = number_match["series"]
        number = number_match["number"].zfill(6)
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"ΤΠ-ΔΑ {series} {number_match['number']}",
            raw_text=text,
            vat_pct=vat_pct,
            lines=tuple(lines),
        )

    def _parse_lines(self, text: str, vat_pct: Decimal) -> list[InvoiceLine]:
        lines: list[InvoiceLine] = []
        in_table = False
        for raw in text.splitlines():
            if re.search(r"ΠΕΡΙΓΡΑΦΗ\s+Μ\.Μ\s+ΠΟΣΟΤΗΣ\s+ΤΙΜΗ", raw):
                in_table = True
                continue
            if TABLE_END_RE.search(raw):
                break
            if not in_table:
                continue
            match = LINE_RE.match(raw)
            if not match:
                continue
            description = greek_upper(match["desc"])
            lines.append(
                InvoiceLine(
                    code=description,
                    description=description,
                    quantity=parse_amount(match["qty"]),
                    unit_price=parse_amount(match["price"]),
                    discount_pct=Decimal("0"),
                    value=parse_amount(match["value"]),
                    vat_pct=vat_pct,
                )
            )
        return lines
