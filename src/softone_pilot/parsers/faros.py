from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, greek_upper, parse_amount

# "   722   ΝΑΥΛΟΣ (ΑΡΘΡΟ 22)      120.00€"  /  "   1   ΠΡΑΚΤΟΡΕΙΑΚΑ      50.00€   24.00"
CHARGE_RE = re.compile(
    r"^\s{5,}(?P<code>\d{1,4})\s{3,}(?P<desc>\S.*?)\s{3,}(?P<amount>\d+\.\d{2})€"
    r"(?:\s+(?P<pct>\d{1,2}\.\d{2}))?\s*$"
)
CONTINUATION_RE = re.compile(r"^\s{20,}(?P<desc>[^\s\d].*?)\s*$")
HEAD_RE = re.compile(
    r"^(?P<kind>ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ|ΕΞΟΔΟΛΟΓΙΟ)\b.*?\s(?P<number>\d{7})\s+"
    r"(?P<date>\d{2}/\d{2}/\d{2})\s*$",
    re.M,
)


def amount_after(text: str, label: str) -> Decimal | None:
    match = re.search(rf"{label}\s+(\d+\.\d{{2}})€", text)
    return parse_amount(match.group(1)) if match else None


class FarosFamilyParser(SupplierParser):
    """Thessaloniki port forwarders sharing one invoicing program (G.T. FAROS, ΤΖΙΑΣΤΙΔΗΣ «ΦΑΡΟΣ»).

    Each charge has a code (722 ναύλος, 1 πρακτορειακά, 14 φορτοεκφορτωτικά, 11 εκτελωνισμός,
    21 δασμοί+φόροι...) used as category for ``line_codes``; a «% ΦΠΑ» column marks taxable
    charges, the rest are exempt. ΕΞΟΔΟΛΟΓΙΟ (duties paid on our behalf) uses the same layout."""

    layout = True

    def matches(self, normalized_text: str) -> bool:
        return f"Α.Φ.Μ.:{self.vat}" in normalized_text or f"ΑΦΜ:{self.vat}" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if re.search(r"ΠΙΣΤΩΤΙΚΟ", text):
            raise PdfParseError(
                f"Πιστωτικό {self.name} — δεν υποστηρίζεται, καταχώριση χειροκίνητα"
            )
        head = HEAD_RE.search(text)
        if not head:
            raise PdfParseError(f"Λείπουν είδος/αριθμός/ημερομηνία {self.name}")

        lines: list[InvoiceLine] = []
        for raw in text.splitlines():
            match = CHARGE_RE.match(raw)
            if match:
                amount = parse_amount(match["amount"])
                pct = Decimal(match["pct"]).normalize() if match["pct"] else Decimal("0")
                lines.append(
                    InvoiceLine(
                        code=match["code"],
                        description=greek_upper(match["desc"].strip()),
                        quantity=Decimal("1"),
                        unit_price=amount,
                        discount_pct=Decimal("0"),
                        value=amount,
                        vat_pct=pct,
                        category=match["code"],
                    )
                )
                continue
            cont = CONTINUATION_RE.match(raw)
            if lines and cont and not re.search(r"\d+Χ\d", cont["desc"]) and len(cont["desc"]) < 40:
                last = lines[-1]
                lines[-1] = InvoiceLine(
                    code=last.code,
                    description=f"{last.description} {greek_upper(cont['desc'])}",
                    quantity=last.quantity,
                    unit_price=last.unit_price,
                    discount_pct=last.discount_pct,
                    value=last.value,
                    vat_pct=last.vat_pct,
                    category=last.category,
                )
            if raw.lstrip().startswith("ΠΑΡΑΤΗΡΗΣΕΙΣ"):
                break
        if not lines:
            raise PdfParseError(f"Δεν βρέθηκαν χρεώσεις {self.name}")

        net = sum((line.value for line in lines), Decimal("0"))
        vat = amount_after(text, r"ΣΥΝΟΛΟ Φ\.Π\.Α\.") or Decimal("0.00")
        total = amount_after(text, "ΓΕΝΙΚΟ ΣΥΝΟΛΟ")
        if total is None:
            raise PdfParseError(f"Λείπει ΓΕΝΙΚΟ ΣΥΝΟΛΟ {self.name}")
        lines_vat = sum(
            ((line.value * line.vat_pct / 100).quantize(Decimal("0.01")) for line in lines),
            Decimal("0"),
        )
        if abs(lines_vat - vat) > Decimal("0.02"):
            raise PdfParseError(f"ΦΠΑ γραμμών {lines_vat:.2f} != ΦΠΑ {self.name} {vat:.2f}")
        self.validate_total(net, vat, total)

        kind = "ΕΞΟΔΟΛΟΓΙΟ" if head["kind"] == "ΕΞΟΔΟΛΟΓΙΟ" else "ΤΠΥ"
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=head["number"],
            document_date=datetime.strptime(head["date"], "%d/%m/%y").date(),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"{kind} {self.name} {head['number']}",
            raw_text=text,
            vat_pct=max(line.vat_pct for line in lines),
            lines=tuple(lines),
        )


class GtFarosParser(FarosFamilyParser):
    vat = "801643693"
    name = "G.T. FAROS S.A."


class TziastidisFarosParser(FarosFamilyParser):
    vat = "041321205"
    name = "ΓΕΩΡΓΙΟΣ ΧΡ ΤΖΙΑΣΤΙΔΗΣ ΦΑΡΟΣ"
