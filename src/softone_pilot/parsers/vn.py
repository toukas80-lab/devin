from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, parse_amount, parse_date

# VN FOOD PROCESSING EQUIPMENT Snc (IT) - intra-community purchase, VAT code NI41 (art. 41, 0%).
# Italian amounts with 3 decimals (154.800,000). In the layout text the discount is often glued
# to the price ("477,00010" = 477,000 at 10%) and a code may be glued to its description
# ("0311KIT SKEWER ..."). Lines without a numeric item code (MANUALE, CE) are free of charge and
# are skipped; the lines-vs-net check guarantees nothing with a value is lost.

LINE_RE = re.compile(
    r"^\s*(?P<code>\d{4}(?:-[A-Z0-9]+)?)\s*(?P<desc>\S.*?)\s{2,}(?P<qty>\d+,\d{2})\s+N\.?\s+"
    r"(?P<price>[\d.]+,\d{3})\s*(?P<disc>\d{1,3})?\s+(?P<amount>[\d.]+,\d{3})\s+(?P<vat>[A-Z0-9]+)\s*$"
)
ROW_LIKE_RE = re.compile(r"\s\d+,\d{2}\s+N\.?\s+[\d.]+,\d{3}")
HEADER_RE = re.compile(
    r"^\s*(?P<number>\d+)\s+(?P<cust>\d{6})\s+(?P<date>\d{2}/\d{2}/\d{4})\s+\d+\s*$", re.M
)
TOTALS_RE = re.compile(
    r"^(?P<vat>[A-Z0-9]+)\s+Cessioni CEE.*?\s(?P<net>[\d.]+,\d{3})\s+"
    r"(?P<tax>[\d.]+,\d{3})\s+(?P<total>[\d.]+,\d{3})\s*$",
    re.M,
)


class VnParser(SupplierParser):
    """VN FOOD PROCESSING EQUIPMENT Snc (purchase of goods, intra-community, 0% VAT)."""

    vat = "IT01844150688"
    name = "VN FOOD PROCESSING EQUIPMENT SNC"
    layout = True

    def matches(self, normalized_text: str) -> bool:
        return "01844150688" in normalized_text and "VNSRL.COM" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if not re.search(r"Fattura\s*/\s*Invoice", text):
            raise PdfParseError("Άγνωστος τύπος παραστατικού VN (όχι Fattura)")
        if re.search(r"nota\s+di\s+credito|credit\s+note", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό VN — δεν υποστηρίζεται, καταχώριση χειροκίνητα")

        header = HEADER_RE.search(text)
        totals = TOTALS_RE.search(text)
        if not header or not totals:
            raise PdfParseError("Λείπουν αριθμός/ημερομηνία ή σύνολα VN")
        net = parse_amount(totals["net"])
        vat = parse_amount(totals["tax"])
        total = parse_amount(totals["total"])
        self.validate_total(net, vat, total)
        if vat != 0 or totals["vat"] != "NI41":
            raise PdfParseError(f"VN με ΦΠΑ {vat:.2f} / {totals['vat']} — αναμένεται NI41 0%")

        lines = self._parse_lines(text)
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές ειδών VN")
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        number = header["number"].zfill(5)
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_date(header["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"VN FATTURA {header['number']}",
            raw_text=text,
            vat_pct=Decimal("0"),
            lines=tuple(lines),
        )

    def _parse_lines(self, text: str) -> list[InvoiceLine]:
        rows = text.splitlines()
        lines: list[InvoiceLine] = []
        for i, raw in enumerate(rows):
            match = LINE_RE.match(raw)
            if not match:
                continue
            if match["vat"] != "NI41":
                raise PdfParseError(f"VN {match['code']}: κωδικός ΦΠΑ {match['vat']} (όχι NI41)")
            desc = [match["desc"].strip()]
            for follow in rows[i + 1 : i + 4]:
                if not follow.strip() or ROW_LIKE_RE.search(follow) or "IVA /" in follow:
                    break
                desc.append(follow.strip())
            qty = parse_amount(match["qty"])
            price = parse_amount(match["price"])
            disc = Decimal(match["disc"] or "0")
            value = parse_amount(match["amount"])
            expected = qty * price * (Decimal("100") - disc) / Decimal("100")
            if abs(expected - value) > Decimal("0.02"):
                raise PdfParseError(f"VN {match['code']}: {qty} x {price} -{disc}% != {value}")
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=" ".join(desc),
                    quantity=qty,
                    unit_price=price,
                    discount_pct=disc,
                    value=value,
                    vat_pct=Decimal("0"),
                )
            )
        return lines
