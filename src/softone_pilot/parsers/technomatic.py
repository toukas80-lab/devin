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

LINE_RE = re.compile(
    r"^\s*(?P<code>\S+)\s{2,}(?P<desc>.+?)\s{2,}(?P<unit>\S+)\s+"
    r"(?P<qty>\d+(?:[.,]\d+)?)\s+(?P<price>[\d.]+,\d{2})\s+"
    r"(?P<disc>\d+(?:[.,]\d+)?)\s+(?P<value>[\d.]+,\d{2})\s*$"
)


class TechnomaticParser(SupplierParser):
    """Epsilon Digital layout used by TECHNOMATIC GROUP IKE (purchase of goods)."""

    vat = "800745478"
    name = "TECHNOMATIC GROUP IKE"
    layout = True

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if self.vat not in text:
            raise PdfParseError(f"Δεν βρέθηκε το ΑΦΜ TECHNOMATIC {self.vat}")

        number_match = re.search(r"Αρ\.\s*Παραστατικού\s+(\S+)\s+(\d+)", text)
        date_text = first_match(text, (r"\b(\d{2}/\d{2}/\d{4})\b",))
        net_text = first_match(text, (r"Άθροισμα\s+([\d.]+,\d{2})",))
        vat_text = first_match(text, (r"\bΦΠΑ\s+([\d.]+,\d{2})",))
        total_text = first_match(text, (r"ΣΥΝΟΛΟ\s+([\d.]+,\d{2})",))
        if not number_match or not date_text or not net_text or not vat_text or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα TECHNOMATIC")

        lines = self._parse_lines(text)
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές ειδών TECHNOMATIC")

        net = parse_amount(net_text)
        vat = parse_amount(vat_text)
        total = parse_amount(total_text)
        self.validate_total(net, vat, total)
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        vat_pct = (vat / net * 100).quantize(Decimal("1")) if net else Decimal("24")
        series, number = number_match.groups()
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"{series} {number}",
            raw_text=text,
            vat_pct=vat_pct,
            lines=tuple(lines),
        )

    def _parse_lines(self, text: str) -> list[InvoiceLine]:
        lines: list[InvoiceLine] = []
        in_table = False
        for raw in text.splitlines():
            if re.search(r"ΚΩΔΙΚΟΣ\s+ΠΕΡΙΓΡΑΦΗ\s+ΠΟΣΟΤΗΤΑ", raw):
                in_table = True
                continue
            if "Σύνολο Ποσότητας" in raw:
                break
            if not in_table:
                continue
            match = LINE_RE.match(raw)
            if not match:
                continue
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=greek_upper(match["desc"]),
                    quantity=Decimal(match["qty"].replace(",", ".")),
                    unit_price=parse_amount(match["price"]),
                    discount_pct=Decimal(match["disc"].replace(",", ".")),
                    value=parse_amount(match["value"]),
                )
            )
        return lines
