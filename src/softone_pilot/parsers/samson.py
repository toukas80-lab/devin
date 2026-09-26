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

# The issuer block (name, AFM) is a bitmap on these Crystal Reports PDFs; the text only
# carries the forwarder's bank accounts, which identify GR SAMSON reliably.
SAMSON_IBANS = (
    "GR2801407220722002002000077",
    "GR9701108400000084047017045",
    "GR3601722610005261023765167",
    "GR7602603500000430200021404",
)

# "01  24,000,00ΝΑΥΛΟΣ ΓΕΡΜΑΝΙΑ - ΣΙΝΔΟΣ 155,00155,00"
#  code  vat%  fx-amount  description  amount-eur  net
CHARGE_RE = re.compile(
    r"^(?P<code>\d{2})\s+(?P<vat>\d{1,2},\d{2})(?P<fx>\d{1,3}(?:\.\d{3})*,\d{2})"
    r"(?P<desc>[^\d\n][^\n]*?)\s*(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2})(?P<net>\d{1,3}(?:\.\d{3})*,\d{2})\s*$",
    re.MULTILINE,
)


class GrSamsonParser(SupplierParser):
    """GR SAMSON ΔΙΑΜΕΤΑΦΟΡΕΣ Α.Ε. freight invoices (series E), EUR, VAT 24%."""

    vat = "999716715"
    name = "GR SAMSON ΔΙΑΜΕΤΑΦΟΡΕΣ Α.Ε."

    def matches(self, normalized_text: str) -> bool:
        return any(iban in normalized_text for iban in SAMSON_IBANS) and (
            "ΔΙΑΜΕΤΑΦΟΡ" in normalized_text
        )

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        if re.search(r"ΠΙΣΤΩΤΙΚ", text):
            raise PdfParseError("Πιστωτικό GR SAMSON — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        if not re.search(r"e-INVOICE SERIES E", text):
            raise PdfParseError("Το GR SAMSON δεν είναι τιμολόγιο σειράς Ε")

        head = re.search(
            r"e-INVOICE SERIES E\s+(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<number>\d+)", text
        )
        if not head:
            raise PdfParseError("Λείπουν αριθμός/ημερομηνία GR SAMSON")
        number = head["number"]

        totals = re.search(
            r"ΣΥΝΟΛΙΚΗ ΑΞΙΑ / TOTAL AMOUNT:\s*(?P<net>[\d.]+,\d{2})\s*(?P<vat>[\d.]+,\d{2})",
            text,
        )
        grand = re.search(r"ANALYSIS\s*(?P<total>[\d.]+,\d{2})", text)
        if not totals or not grand:
            raise PdfParseError("Λείπουν σύνολα GR SAMSON")
        net = parse_amount(totals["net"])
        vat = parse_amount(totals["vat"])
        total = parse_amount(grand["total"])
        self.validate_total(net, vat, total)
        vat_pct = self.uniform_vat_pct(net, vat)

        consignor = first_match(text, (r"ΑΠΟΣΤΟΛΕΑΣ / CONSIGNOR\s*\n([^\n]+)",)) or ""

        lines: list[InvoiceLine] = []
        for match in CHARGE_RE.finditer(text):
            value = parse_amount(match["net"])
            line_vat = parse_amount(match["vat"])
            if line_vat != vat_pct:
                raise PdfParseError(f"Γραμμή GR SAMSON με ΦΠΑ {line_vat}% (αναμενόταν {vat_pct}%)")
            lines.append(
                InvoiceLine(
                    code="",
                    description=greek_upper(match["desc"]),
                    quantity=Decimal("1"),
                    unit_price=value,
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=vat_pct,
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές εξόδων GR SAMSON")
        lines_net = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_net - net) > Decimal("0.02"):
            raise PdfParseError(f"Το σύνολο γραμμών {lines_net:.2f} != καθαρή αξία {net:.2f}")

        description = " ".join(
            part for part in (greek_upper(consignor), lines[0].description) if part
        )
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number,
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=description,
            raw_text=text,
            vat_pct=vat_pct,
            lines=tuple(lines),
        )
