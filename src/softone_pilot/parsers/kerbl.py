from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, first_match

# Albert Kerbl GmbH (DE) - intra-community purchase of goods, 0% VAT ("tax free intracommunity
# delivery"). Amounts are English style (1,350.00), dates DD/MM/YY. Cartridges are invoiced per
# "package" of 50 pcs; SoftOne stocks them per piece, so qty*50 and price/50 (13.50 -> 0.27).

LINE_RE = re.compile(
    r"^\s*\d+\s+(?P<code>\d{4,6})\s{2,}(?P<qty>[\d,]+)\s+(?P<unit>package|pcs|piece)\s+"
    r"(?P<price>[\d,]+\.\d{2})\s+(?P<value>[\d,]+\.\d{2})\s*$",
    re.IGNORECASE,
)
PCS_PER_BOX_RE = re.compile(r"(\d+)\s*pcs/box", re.IGNORECASE)


def parse_en_amount(value: str) -> Decimal:
    return Decimal(value.replace(",", "")).quantize(Decimal("0.01"))


class KerblParser(SupplierParser):
    """Albert Kerbl GmbH (purchase of goods, intra-community, 0% VAT)."""

    vat = "DE129226311"
    name = "ALBERT KERBL GMBH"
    layout = True

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if "DE129226311" not in text.replace(" ", ""):
            raise PdfParseError("Δεν βρέθηκε το VAT KERBL DE129226311")
        if not re.search(r"\bInvoice\b", text):
            raise PdfParseError("Άγνωστος τύπος παραστατικού KERBL (όχι Invoice)")
        if re.search(r"credit\s*(note|memo)", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό KERBL — δεν υποστηρίζεται, καταχώριση χειροκίνητα")

        number = first_match(text, (r"Invoice No\.\s+(VR-\d+)",))
        date_text = first_match(text, (r"\bDate\s+(\d{2}/\d{2}/\d{2})\b",))
        net_text = first_match(text, (r"Total EUR Excl\. VAT\s+([\d,]+\.\d{2})",))
        vat_text = first_match(text, (r"Tax Amount\s+([\d,]+\.\d{2})",))
        total_text = first_match(text, (r"Total EUR Incl\. VAT\s+([\d,]+\.\d{2})",))
        if not number or not date_text or not net_text or not vat_text or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα KERBL")

        net = parse_en_amount(net_text)
        vat = parse_en_amount(vat_text)
        total = parse_en_amount(total_text)
        self.validate_total(net, vat, total)
        if vat != 0 or not re.search(r"intracommunity delivery", text, re.IGNORECASE):
            raise PdfParseError(f"KERBL με ΦΠΑ {vat:.2f} — αναμένεται ενδοκοινοτικό 0%")

        lines = self._parse_lines(text)
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές ειδών KERBL")
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=self._parse_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"KERBL {number}",
            raw_text=text,
            vat_pct=Decimal("0"),
            lines=tuple(lines),
        )

    @staticmethod
    def _parse_date(value: str) -> date:
        return datetime.strptime(value, "%d/%m/%y").date()

    def _parse_lines(self, text: str) -> list[InvoiceLine]:
        rows = text.splitlines()
        lines: list[InvoiceLine] = []
        for i, raw in enumerate(rows):
            match = LINE_RE.match(raw)
            if not match:
                continue
            block: list[str] = []
            for follow in rows[i + 1 : i + 4]:
                if not follow.strip() or LINE_RE.match(follow):
                    break
                block.append(follow.strip())
            description = " ".join(b for b in block if not b.startswith("Tariff No."))
            qty = Decimal(match["qty"].replace(",", ""))
            price = parse_en_amount(match["price"])
            value = parse_en_amount(match["value"])
            pcs = PCS_PER_BOX_RE.search(description)
            if match["unit"].lower() == "package" and pcs:
                per_box = Decimal(pcs.group(1))
                qty, price = qty * per_box, price / per_box
            if abs(qty * price - value) > Decimal("0.02"):
                raise PdfParseError(f"KERBL {match['code']}: {qty} x {price} != {value}")
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=description,
                    quantity=qty,
                    unit_price=price,
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=Decimal("0"),
                )
            )
        return lines
