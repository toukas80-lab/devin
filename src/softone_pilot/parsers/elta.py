from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData
from softone_pilot.parsers.base import (
    PdfParseError,
    SupplierParser,
    parse_amount,
    parse_date,
)

# The issuer block (name, AFM, logo) is a bitmap; the text carries the billing department's
# phone, the document-type code 021 (ΤΠΥ) and the RF payment code.
ELTA_MARKERS = (
    "ΤΜΗΜΑΤΟΣΤΙΜΟΛΟΓΗΣΗΣ:2106073030",
    "ΠΑΡΑΣΤΑΤΙΚΟΎ(021)",
    "ΚΩΔΙΚΟΣΗΛΕΚΤΡΟΝΙΚΗΣΠΛΗΡΩΜΗΣ",
)

HEAD_RE = re.compile(
    r"^(?P<kind>ΤΙΜΟΛΟΓΙΟ[^\n]*?|ΠΙΣΤΩΤΙΚΟ[^\n]*?)[ \t]+(?P<series>\S+)[ \t]+(?P<number>\d+)[ \t]+"
    r"(?P<date>\d{2}/\d{2}/\d{4})[ \t]*$",
    re.MULTILINE,
)

# "201 ΠΟΛΗ ΠΟΛΗ - ΠΠ    9    53.70    [disc]    53.70    24.00"
CHARGE_RE = re.compile(
    r"^(?P<code>\d{3})[ \t]+(?P<desc>\S[^\n]*?)[ \t]{2,}(?P<qty>\d+)[ \t]+(?P<gross>[\d.,]+)[ \t]+"
    r"(?:(?P<disc>[\d.,]+)[ \t]+)?(?P<value>[\d.,]+)[ \t]+(?P<vat>\d{1,2}\.\d{2})[ \t]*$",
    re.MULTILINE,
)
TOTAL_RE = re.compile(r"^(?P<total>[\d.,]+)\s*\n\*?RF\d", re.MULTILINE)
MONTH_GENITIVE = (
    "ΙΑΝΟΥΑΡΙΟΥ",
    "ΦΕΒΡΟΥΑΡΙΟΥ",
    "ΜΑΡΤΙΟΥ",
    "ΑΠΡΙΛΙΟΥ",
    "ΜΑΙΟΥ",
    "ΙΟΥΝΙΟΥ",
    "ΙΟΥΛΙΟΥ",
    "ΑΥΓΟΥΣΤΟΥ",
    "ΣΕΠΤΕΜΒΡΙΟΥ",
    "ΟΚΤΩΒΡΙΟΥ",
    "ΝΟΕΜΒΡΙΟΥ",
    "ΔΕΚΕΜΒΡΙΟΥ",
)


def elta_amount(value: str) -> Decimal:
    """ELTA prints US-style numbers: 1,234.50."""
    return parse_amount(value.replace(",", ""))


class EltaCourierParser(SupplierParser):
    """ΤΑΧΥΜΕΤΑΦΟΡΕΣ ΕΛΤΑ Α.Ε. (ELTA Courier) monthly service invoices, EUR, VAT 24%."""

    vat = "099759170"
    name = "ΤΑΧΥΜΕΤΑΦΟΡΕΣ ΕΛΤΑ ΑΝΩΝΥΜΟΣ ΕΤΑΙΡΕΙΑ"

    def matches(self, normalized_text: str) -> bool:
        return all(marker in normalized_text for marker in ELTA_MARKERS)

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(text)
        head = HEAD_RE.search(text)
        if not head:
            raise PdfParseError("Λείπουν είδος/αριθμός/ημερομηνία παραστατικού ΕΛΤΑ")
        if head["kind"].startswith("ΠΙΣΤΩΤΙΚΟ"):
            raise PdfParseError("Πιστωτικό ΕΛΤΑ — δεν υποστηρίζεται, καταχώριση χειροκίνητα")

        charges = list(CHARGE_RE.finditer(text))
        if not charges:
            raise PdfParseError("Δεν βρέθηκαν γραμμές υπηρεσιών ΕΛΤΑ")
        net = sum((elta_amount(m["value"]) for m in charges), Decimal("0"))
        shipments = sum(int(m["qty"]) for m in charges)
        vat_pcts = {Decimal(m["vat"]).quantize(Decimal("1")) for m in charges}
        if len(vat_pcts) != 1:
            raise PdfParseError(f"Μεικτός ΦΠΑ στις γραμμές ΕΛΤΑ: {sorted(vat_pcts)}")
        vat_pct = vat_pcts.pop()

        total_match = TOTAL_RE.search(text)
        if not total_match:
            raise PdfParseError("Λείπει το πληρωτέο σύνολο ΕΛΤΑ")
        total = elta_amount(total_match["total"])
        vat = (total - net).quantize(Decimal("0.01"))
        if abs(net * vat_pct / 100 - vat) > Decimal("0.02"):
            raise PdfParseError(
                f"Ο ΦΠΑ {vat:.2f} δεν είναι {vat_pct}% του {net:.2f} (σύνολο {total:.2f})"
            )

        document_date = parse_date(head["date"])
        month = MONTH_GENITIVE[document_date.month - 1]
        description = f"ΜΕΤΑΦΟΡΙΚΑ {month} {document_date.year} - {shipments} ΑΠΟΣΤΟΛΕΣ ΕΛΤΑ"
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=head["number"],
            document_date=document_date,
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=description,
            raw_text=text,
            vat_pct=vat_pct,
        )
