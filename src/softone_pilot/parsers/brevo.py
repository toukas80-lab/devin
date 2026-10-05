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

# "Starter plan monthly 1 €7.000 % €7.00"  /  "1 €7.000 % €7.00" (description on the line above)
# "Recurring emails monthly 20000 - 0 % €18.00"
ITEM_RE = re.compile(
    r"^(?P<desc>.*?)\s*(?:(?P<qty>\d+)\s+€[\d,]+\.\d{2}|-)\s*(?P<tax>\d+)\s*%\s+€(?P<value>[\d,]+\.\d{2})\s*$"
)


def parse_brevo_date(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%b %d, %Y").date()
    except ValueError as exc:
        raise PdfParseError(f"Μη έγκυρη ημερομηνία: {value}") from exc


class BrevoParser(SupplierParser):
    """Sendinblue / Brevo (France) EUR invoices, reverse charge (VAT 0%)."""

    vat = "FR80498019298"
    name = "BREVO - SENDINBLUE"

    def matches(self, normalized_text: str) -> bool:
        return "FR80498019298" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = text.replace("\xa0", " ").replace("\x00", " ").replace("—", " ")
        self.reject_proforma(text)
        if re.search(r"Credit note|Refund", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό BREVO — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        if not re.search(r"reverse charge", text, re.IGNORECASE):
            raise PdfParseError("Το τιμολόγιο BREVO δεν αναφέρει reverse charge")

        number = first_match(text, (r"Invoice #\s*(SIB-\d+)",))
        date_text = first_match(text, (r"Invoice Date\s*([A-Za-z]{3} \d{1,2}, \d{4})",))
        total_text = first_match(text, (r"(?m)^Total\s+€([\d,]+\.\d{2})\s*$",))
        if not number or not date_text or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολο BREVO")
        if "(EUR)" not in text:
            raise PdfParseError("Το τιμολόγιο BREVO δεν είναι σε EUR")

        lines: list[InvoiceLine] = []
        previous = ""
        in_table = False
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("DESCRIPTION"):
                in_table = True
                continue
            if not in_table or not line:
                continue
            if line.startswith("Total"):
                break
            match = ITEM_RE.match(line)
            if not match:
                previous = line
                continue
            if match["tax"] != "0":
                raise PdfParseError(f"Γραμμή BREVO με ΦΠΑ {match['tax']}%")
            desc = match["desc"].strip() or previous
            value = parse_amount(match["value"])
            qty = Decimal(match["qty"] or "1")
            lines.append(
                InvoiceLine(
                    code="",
                    description=greek_upper(desc),
                    quantity=qty,
                    unit_price=value / qty,
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=Decimal("0"),
                )
            )
            previous = ""
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές BREVO")

        net = sum((line.value for line in lines), Decimal("0"))
        total = parse_amount(total_text)
        self.validate_total(net, Decimal("0"), total)

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_brevo_date(date_text),
            net_value=net,
            vat_value=Decimal("0.00"),
            total_value=total,
            description=f"BREVO {lines[0].description}",
            raw_text=text,
            vat_pct=Decimal("0"),
            lines=tuple(lines),
        )
