from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, parse_date

HEAD_RE = re.compile(
    r"Fatura / Invoice.*?\n.*?\n\s+FT (?P<year>\d{4})/(?P<seq>\d+)\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+EUR"
)
LINE_RE = re.compile(
    r"^(?P<code>[A-Z0-9][A-Z0-9-]{3,})\s{3,}(?P<desc>\S.*?)\s{3,}(?P<qty>[\d,]*\d\.\d{2})\s+un\s+"
    r"(?P<price>[\d,]*\d\.\d{2})\s+(?P<vat>\d{1,2})%\s+(?:(?P<disc>\d+(?:\.\d+)?)\s+)?(?P<amount>[\d,]*\d\.\d{2})\s*$",
    re.M,
)


def amount(value: str) -> Decimal:
    try:
        return Decimal(value.replace(",", "")).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise PdfParseError(f"Μη έγκυρο ποσό: {value}") from exc


def amount_after(text: str, label: str) -> Decimal:
    match = re.search(rf"{label}\s+([\d,]*\d\.\d{{2}})", text)
    if not match:
        raise PdfParseError(f"Λείπει «{label}» AEGIMESH")
    return amount(match.group(1))


class AegimeshParser(SupplierParser):
    """AEGImesh, Lda (PT) — protective gloves, intra-community purchase exempt (art.14 RITI, 0%)."""

    vat = "PT515294640"
    name = "AEGIMESH, LDA"
    layout = True

    def matches(self, normalized_text: str) -> bool:
        return "AEGIMESH" in normalized_text and "515294640" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if re.search(r"Nota de cr[eé]dito|Credit note", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό AEGIMESH — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        if not head:
            raise PdfParseError("Λείπουν αριθμός/ημερομηνία AEGIMESH (δεχόμαστε μόνο FT)")
        net = amount_after(text, r"Total Líquido / Net Total")
        vat = amount_after(text, r"Total IVA / VAT")
        total = amount_after(text, r"\n\s+Total")
        self.validate_total(net, vat, total)
        if vat != 0:
            raise PdfParseError(f"AEGIMESH με ΦΠΑ {vat:.2f} — αναμένεται ενδοκοινοτική 0%")

        lines: list[InvoiceLine] = []
        for match in LINE_RE.finditer(text):
            if match["vat"] != "0" or match["disc"]:
                raise PdfParseError(
                    f"AEGIMESH {match['code']}: ΦΠΑ/έκπτωση γραμμής δεν υποστηρίζεται"
                )
            qty, price, value = (
                amount(match["qty"]),
                amount(match["price"]),
                amount(match["amount"]),
            )
            if abs(qty * price - value) > Decimal("0.02"):
                raise PdfParseError(f"AEGIMESH {match['code']}: {qty} x {price} != {value}")
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=match["desc"].strip(),
                    quantity=qty,
                    unit_price=price,
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=Decimal("0"),
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές AEGIMESH")
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        number = f"FT{head['year']}-{head['seq']}"
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"AEGIMESH {number}",
            raw_text=text,
            vat_pct=Decimal("0"),
            lines=tuple(lines),
        )
