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

# "1 Maker Subscription, renewed monthly renewal for 13139. 1 17.50"
ITEM_RE = re.compile(
    r"^(?P<num>\d+) (?P<desc>[A-Za-z][^\n]*?)\s+(?P<qty>\d+)\s+(?P<value>[\d,]+\.\d{2})\s*$",
    re.MULTILINE,
)
# "2 Tax rate: 24%\n...\n1 4.20"
TAX_RE = re.compile(
    r"^\d+ Tax rate: (?P<pct>\d+)%\n(?:[^\n]*\n)*?(?P<qty>\d+) (?P<value>[\d,]+\.\d{2})\s*$",
    re.MULTILINE,
)


def parse_uk_date(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%d %b %Y").date()
    except ValueError as exc:
        raise PdfParseError(f"Μη έγκυρη ημερομηνία: {value}") from exc


class CarvecoParser(SupplierParser):
    """Carveco Ltd (UK) USD subscription invoices; Greek VAT charged via EU OSS."""

    vat = "CARVECO"
    name = "CARVECO LTD"

    def matches(self, normalized_text: str) -> bool:
        return "CARVECOLTD" in normalized_text or "GB307946483" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = text.replace("\xa0", " ").replace("\x00", " ")
        self.reject_proforma(text)
        if re.search(r"Credit note|Refund", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό CARVECO — δεν υποστηρίζεται, καταχώριση χειροκίνητα")

        number = first_match(text, (r"Inv#\s*(\d+)",))
        date_text = first_match(text, (r"Invoice Date\s*:\s*(\d{1,2} [A-Za-z]{3} \d{4})",))
        total_text = first_match(text, (r"Total USD\$([\d,]+\.\d{2})",))
        if not number or not date_text or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολο CARVECO")
        if not re.search(r"Amount \(USD\$\)", text):
            raise PdfParseError("Το τιμολόγιο CARVECO δεν είναι σε USD")

        tax_match = TAX_RE.search(text)
        if not tax_match:
            raise PdfParseError("Δεν βρέθηκε γραμμή φόρου CARVECO")
        vat_pct = Decimal(tax_match["pct"])
        vat = parse_amount(tax_match["value"])

        lines: list[InvoiceLine] = []
        for match in ITEM_RE.finditer(text):
            if match.start() >= tax_match.start():
                break
            value = parse_amount(match["value"])
            desc = re.sub(r",?\s*renewed monthly renewal for\s+(\d+)", r" (\1)", match["desc"])
            lines.append(
                InvoiceLine(
                    code="",
                    description=greek_upper(desc.rstrip(". ")),
                    quantity=Decimal(match["qty"]),
                    unit_price=value / Decimal(match["qty"]),
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=vat_pct,
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές CARVECO")

        net = sum((line.value for line in lines), Decimal("0"))
        total = parse_amount(total_text)
        self.validate_total(net, vat, total)
        if self.uniform_vat_pct(net, vat) != vat_pct:
            raise PdfParseError(f"Ο φόρος {vat:.2f} δεν είναι {vat_pct}% του {net:.2f}")

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_uk_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"CARVECO {lines[0].description}",
            raw_text=text,
            vat_pct=vat_pct,
            lines=tuple(lines),
            currency="USD",
        )
