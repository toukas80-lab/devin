from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import (
    PdfParseError,
    SupplierParser,
    first_match,
    greek_upper,
    parse_amount,
)

# "Overage credits 1 $20.00 0% $20.00"
ITEM_RE = re.compile(
    r"^(?P<desc>.+?)\s+(?P<qty>\d+)\s+\$(?P<price>[\d,]+\.\d{2})\s+(?P<tax>\d+)%\s+"
    r"\$(?P<value>[\d,]+\.\d{2})\s*$",
    re.MULTILINE,
)


def parse_us_date(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%B %d, %Y").date()
    except ValueError as exc:
        raise PdfParseError(f"Μη έγκυρη ημερομηνία: {value}") from exc


class CognitionParser(SupplierParser):
    """Cognition AI (Devin) USD invoices, reverse charge, no Greek AFM on the PDF."""

    vat = "COGNITION"
    name = "COGNITION AI INC - DEVIN"

    def matches(self, normalized_text: str) -> bool:
        return "COGNITIONAIINC" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = text.replace("\xa0", " ").replace("\x00", " ")
        self.reject_proforma(text)
        if re.search(r"Credit note|Refund", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό COGNITION — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        if not re.search(r"reverse charge", text, re.IGNORECASE):
            raise PdfParseError("Το τιμολόγιο COGNITION δεν αναφέρει reverse charge")

        number_match = re.search(r"Invoice number\s+(?P<prefix>[A-Z0-9]+)[ -](?P<suffix>\d+)", text)
        date_text = first_match(text, (r"Date of issue\s+([A-Za-z]+ \d{1,2}, \d{4})",))
        total_text = first_match(text, (r"Amount due\s+\$([\d,]+\.\d{2})\s+USD",))
        subtotal_text = first_match(text, (r"Subtotal\s+\$([\d,]+\.\d{2})",))
        if not number_match or not date_text or not total_text or not subtotal_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα COGNITION")

        total = parse_amount(total_text)
        net = parse_amount(subtotal_text)
        if total != net:
            raise PdfParseError(f"Το COGNITION περιέχει φόρο: {net:.2f} != {total:.2f}")

        lines: list[InvoiceLine] = []
        for match in ITEM_RE.finditer(text):
            if match["tax"] != "0":
                raise PdfParseError(f"Γραμμή COGNITION με φόρο {match['tax']}%")
            value = parse_amount(match["value"])
            lines.append(
                InvoiceLine(
                    code="",
                    description=greek_upper(match["desc"]),
                    quantity=Decimal(match["qty"]),
                    unit_price=parse_amount(match["price"]),
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=Decimal("0"),
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές COGNITION")
        lines_net = sum((line.value for line in lines), Decimal("0"))
        if lines_net != net:
            raise PdfParseError(f"Άθροισμα γραμμών {lines_net:.2f} != subtotal {net:.2f}")

        # Historical SoftOne numbering: ZZCYINBS 0078 -> ZZCYINBS-78
        document_number = f"{number_match['prefix']}-{number_match['suffix'].lstrip('0') or '0'}"
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=document_number,
            document_date=parse_us_date(date_text),
            net_value=net,
            vat_value=Decimal("0.00"),
            total_value=total,
            description=f"DEVIN {lines[0].description}",
            raw_text=text,
            vat_pct=Decimal("0"),
            lines=tuple(lines),
            currency="USD",
        )
