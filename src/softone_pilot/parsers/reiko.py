from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, first_match

# "1.1   60   Piece   10007"
ITEM_RE = re.compile(r"^\d+(?:\.\d+)?\s+(?P<qty>[\d,]+)\s+(?P<unit>[A-Za-z]+)\s+(?P<code>\S+)\s*$")
# "   aproLin® -L90- Apron, ...   7.700   0   0   462.00"  (transport line has no unit price)
DETAIL_RE = re.compile(
    r"^\s+(?P<desc>\S.*?)\s{2,}(?:(?P<price>[\d,]+\.\d{2,3})\s+)?(?P<vat>\d+)\s+"
    r"(?P<disc>[\d.]+)\s+(?P<value>[\d,]+\.\d{2})\s*$"
)


def parse_en(value: str) -> Decimal:
    return Decimal(value.replace(",", ""))


class ReikoParser(SupplierParser):
    """ReiKo aproTex GmbH — intra-community purchase of aprons (0% VAT, EUR, 1,234.56 style)."""

    vat = "PL5263671757"
    name = "REIKO APROTEX GMBH"
    layout = True

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if re.search(r"credit\s*note|gutschrift", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό REIKO — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        number = first_match(text, (r"I N V O I C E\s+Nr\.\s+(\d+)",))
        date_text = first_match(text, (r"(?m)^Date\s+:\s+(\d{2}\.\d{2}\.\d{4})",))
        net_text = first_match(text, (r"(?m)^Net amount\b.*?([\d,]+\.\d{2})\s*$",))
        gross_text = first_match(text, (r"(?m)^Gross invoice amount\s+EUR\s+([\d,]+\.\d{2})",))
        if not number or not date_text or not net_text or not gross_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα REIKO")
        net = parse_en(net_text)
        gross = parse_en(gross_text)
        if net != gross or not re.search(r"intra-Community supply", text, re.IGNORECASE):
            raise PdfParseError(f"REIKO με ΦΠΑ {gross - net:.2f} — αναμένεται ενδοκοινοτικό 0%")

        lines = self._parse_lines(text)
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές ειδών REIKO")
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=datetime.strptime(date_text, "%d.%m.%Y").date(),
            net_value=net,
            vat_value=Decimal("0"),
            total_value=gross,
            description=f"REIKO {number}",
            raw_text=text,
            vat_pct=Decimal("0"),
            lines=tuple(lines),
        )

    @staticmethod
    def _parse_lines(text: str) -> list[InvoiceLine]:
        rows = text.splitlines()
        lines: list[InvoiceLine] = []
        for i, raw in enumerate(rows):
            item = ITEM_RE.match(raw)
            if not item:
                continue
            detail = next((m for m in (DETAIL_RE.match(r) for r in rows[i + 1 : i + 4]) if m), None)
            if not detail:
                raise PdfParseError(f"REIKO {item['code']}: δεν βρέθηκε τιμή/αξία")
            qty = parse_en(item["qty"])
            value = parse_en(detail["value"])
            disc = Decimal(detail["disc"])
            price = parse_en(detail["price"]) if detail["price"] else value / qty
            if Decimal(detail["vat"]) != 0:
                raise PdfParseError(f"REIKO {item['code']}: ΦΠΑ {detail['vat']}% — αναμένεται 0")
            if abs(qty * price * (100 - disc) / 100 - value) > Decimal("0.02"):
                raise PdfParseError(f"REIKO {item['code']}: {qty} x {price} != {value}")
            lines.append(
                InvoiceLine(
                    code=item["code"],
                    description=detail["desc"],
                    quantity=qty,
                    unit_price=price.quantize(Decimal("0.01")),
                    discount_pct=disc,
                    value=value.quantize(Decimal("0.01")),
                    vat_pct=Decimal("0"),
                )
            )
        return lines
