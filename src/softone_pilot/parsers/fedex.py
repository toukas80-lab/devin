from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import (
    PdfParseError,
    SupplierParser,
    first_match,
    parse_amount,
    parse_date,
)

# "62.7102/09/2026876620512035 0.00 62.71FedEx Intl Priority 1 6.70 kg"
SHIPMENT_RE = re.compile(
    r"^(?P<value>\d+\.\d{2})(?P<date>\d{2}/\d{2}/\d{4})(?P<awb>\d{12})\s+"
    r"(?P<a>\d+\.\d{2})\s+(?P<b>\d+\.\d{2})(?P<service>FedEx[^\d\n]*?)\s+\d+\s+[\d.]+\s*kg",
    re.MULTILINE,
)
VAT_PCT_RE = re.compile(r"Ισχύον ΦΠΑ\s+(\d+(?:\.\d+)?)%")


class FedexParser(SupplierParser):
    vat = "095283423"
    name = "FEDEX EXPRESS GREECE ΜΟΝΟΠΡΟΣΩΠΗ ΕΠΕ"

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = text.replace("\xa0", " ")
        if re.search(r"Πιστωτικό|Credit Note", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό FEDEX — δεν υποστηρίζεται, καταχώριση χειροκίνητα")

        header = re.search(r"^(\d{9})\n(\d{2}/\d{2}/\d{4})\n", text, re.MULTILINE)
        total_text = first_match(text, (r"Συνολική Αξία\s+EUR\s+([\d.]+)", r"([\d.]+)\s+EUR\b"))
        net_text = first_match(text, (r"Καθαρή Αξία\s*\n\s*-?[\d.]+\s+([\d.]+)",))
        if not header or not total_text or not net_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα FEDEX")

        total = parse_amount(total_text)
        net = parse_amount(net_text)
        vat = total - net

        lines = self._parse_shipments(text)
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν αποστολές FEDEX")
        lines_net = sum((line.value for line in lines), Decimal("0"))
        lines_vat = sum(
            ((line.value * line.vat_pct / 100).quantize(Decimal("0.01")) for line in lines),
            Decimal("0"),
        )
        if abs(lines_net - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα αποστολών {lines_net:.2f} != καθαρή αξία {net:.2f}")
        if abs(lines_vat - vat) > Decimal("0.02") * len(lines):
            raise PdfParseError(f"ΦΠΑ αποστολών {lines_vat:.2f} != ΦΠΑ τιμολογίου {vat:.2f}")

        number, date_text = header.groups()
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"ΜΕΤΑΦΟΡΙΚΑ FEDEX {len(lines)} ΑΠΟΣΤΟΛΕΣ",
            raw_text=text,
            vat_pct=lines[0].vat_pct,
            lines=tuple(lines),
        )

    def _parse_shipments(self, text: str) -> list[InvoiceLine]:
        blocks = re.split(r"ΥπηρεσίαΑρ\. Αποστολής", text)[1:]
        lines: list[InvoiceLine] = []
        for block in blocks:
            match = SHIPMENT_RE.search(block)
            if not match:
                continue
            pct_match = VAT_PCT_RE.search(block)
            vat_pct = Decimal(pct_match.group(1)).normalize() if pct_match else Decimal("0")
            value = parse_amount(match["value"])
            service = re.sub(r"\s+", " ", match["service"]).strip().upper()
            lines.append(
                InvoiceLine(
                    code=match["awb"],
                    description=f"{service} {match['awb']} {match['date']}",
                    quantity=Decimal("1"),
                    unit_price=value,
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=vat_pct,
                )
            )
        return lines
