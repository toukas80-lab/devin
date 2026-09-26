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

# Freight: "62.7102/09/2026876620512035 0.00 62.71FedEx Intl Priority 1 6.70 kg"
# Duty:    "10/06/2026872826082908 39.23 53.04Economy Service 13.81 0.00 0.00"
# The shipment total is the amount glued to the service name.
SHIPMENT_RE = re.compile(
    r"(?P<date>\d{2}/\d{2}/\d{4})(?P<awb>\d{12})[^\n]*?\s(?P<value>\d+\.\d{2})"
    r"(?P<service>[A-Za-z][A-Za-z ]*?)\s+\d"
)
VAT_PCT_RE = re.compile(r"Ισχύον ΦΠΑ\s+(\d+(?:\.\d+)?)%")
# "Έκπτωση Καθαρή Αξία" is followed by one "<discount> <net>" row per VAT rate.
NET_ROWS_RE = re.compile(r"Καθαρή Αξία\s*\n((?:-?\d+\.\d{2} \d+\.\d{2}\n)+)")
DUTY_TITLE = "Απόδειξη Δασμών"
DUTY_VAT_RE = re.compile(r"ΦΠΑ σε [\d.]+ % (\d+\.\d{2})")
DUTY_CATEGORY = "duty"
# "-225.63FOUNTOUKAS THEODOROS STOCKHOLM COUNTY, SWEDEN Εκπτωση": sender first, then recipient.
SENDER_RE = re.compile(r"Αποστολέας Παραλήπτης[^\n]*\n-?[\d.]+(?P<sender>[A-Z][A-Z.&'-]*)")
OWN_NAME = "FOUNTOUKA"


def shipment_category(block: str, vat_pct: Decimal) -> str:
    match = SENDER_RE.search(block)
    if not match:
        raise PdfParseError("Δεν βρέθηκε αποστολέας σε αποστολή FEDEX")
    direction = "export" if OWN_NAME in match["sender"].upper() else "import"
    return f"{direction}{vat_pct}"


class FedexParser(SupplierParser):
    vat = "095283423"
    name = "FEDEX EXPRESS GREECE ΜΟΝΟΠΡΟΣΩΠΗ ΕΠΕ"

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = text.replace("\xa0", " ")
        if re.search(r"Πιστωτικό|Credit Note", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό FEDEX — δεν υποστηρίζεται, καταχώριση χειροκίνητα")

        duty = DUTY_TITLE in text
        header = re.search(r"^(\d{9})\n(\d{2}/\d{2}/\d{4})\n", text, re.MULTILINE)
        total_text = first_match(text, (r"Συνολική Αξία\s+EUR\s+([\d.]+)", r"([\d.]+)\s+EUR\b"))
        if not header or not total_text:
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα FEDEX")
        total = parse_amount(total_text)

        if duty:
            vat_text = first_match(text, (DUTY_VAT_RE.pattern,))
            if vat_text is None:
                raise PdfParseError("Λείπει ΦΠΑ σε απόδειξη δασμών FEDEX")
            vat = parse_amount(vat_text)
            if vat != 0:
                raise PdfParseError("Απόδειξη δασμών FEDEX με ΦΠΑ — καταχώριση χειροκίνητα")
            net = total
        else:
            rows = NET_ROWS_RE.search(text)
            if not rows:
                raise PdfParseError("Λείπει καθαρή αξία FEDEX")
            net = sum(
                (parse_amount(row.split()[1]) for row in rows.group(1).splitlines()),
                Decimal("0"),
            )
            vat = total - net

        lines = self._parse_shipments(text, duty)
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
            description=f"{'ΔΑΣΜΟΙ' if duty else 'ΜΕΤΑΦΟΡΙΚΑ'} FEDEX {len(lines)} ΑΠΟΣΤΟΛΕΣ",
            raw_text=text,
            vat_pct=lines[0].vat_pct,
            lines=tuple(lines),
        )

    def _parse_shipments(self, text: str, duty: bool) -> list[InvoiceLine]:
        blocks = re.split(r"ΥπηρεσίαΑρ\. Αποστολής", text)[1:]
        lines: list[InvoiceLine] = []
        for block in blocks:
            match = SHIPMENT_RE.search(block)
            if not match:
                continue
            service = match["service"].strip().upper()
            value = parse_amount(match["value"])
            if duty:
                vat_pct = Decimal("0")
                category = DUTY_CATEGORY
                description = f"{service} {match['awb']} {match['date']} ΔΑΣΜΟΙ"
            else:
                pct_match = VAT_PCT_RE.search(block)
                vat_pct = Decimal(pct_match.group(1)).normalize() if pct_match else Decimal("0")
                category = shipment_category(block, vat_pct)
                description = f"{service} {match['awb']} {match['date']}"
            lines.append(
                InvoiceLine(
                    code=match["awb"],
                    description=description,
                    quantity=Decimal("1"),
                    unit_price=value,
                    discount_pct=Decimal("0"),
                    value=value,
                    vat_pct=vat_pct,
                    category=category,
                )
            )
        return lines
