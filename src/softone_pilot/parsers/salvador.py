from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import PdfParseError, SupplierParser, parse_amount, parse_date

# "101PT155020 LAMA SEGAOSSA TEMP. D6 MM.1550-20X0,48 10,00 NR 3,46 34,60 INTR"
LINE_RE = re.compile(
    r"^\s*(?P<code>\d{3}PT\d{6})\s+(?P<desc>\S.*?)\s+(?P<qty>[\d.]+,\d{2})\s+NR\s+"
    r"(?P<price>[\d.]+,\d{2})\s+(?:(?P<disc>\d{1,2}(?:,\d+)?)\s+)?(?P<amount>[\d.]+,\d{2})\s+"
    r"(?P<vat>[A-Z0-9]+)\s*$",
    re.M,
)
HEAD_RE = re.compile(r"^\s*(?P<number>\d{6})\s+(?P<date>\d{2}/\d{2}/\d{4})\s+\d+\s*$", re.M)


def amount_after(text: str, label: str) -> Decimal:
    match = re.search(rf"{label}\s+([\d.]+,\d{{2}})", text)
    if not match:
        raise PdfParseError(f"Λείπει «{label}» SALVADOR")
    return parse_amount(match.group(1))


class SalvadorParser(SupplierParser):
    """gi-ESSE SALVADOR Srl (IT) — band-saw blades, intra-community purchase (INTR, art.41, 0%).

    A header discount («Ulteriori sconti», e.g. 3% before departure) reduces every line; it is
    applied as the line discount so the lines add up to «Totale imponibile»."""

    vat = "IT01732090939"
    name = "GI-ESSE SALVADOR SRL"
    layout = True

    def matches(self, normalized_text: str) -> bool:
        return "01732090939" in normalized_text and "SALVADOR" in normalized_text

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        self.reject_proforma(re.sub(r"Fattura ProForma Nr\.[^\n]*", "", text))
        if re.search(r"nota\s+di\s+credito|credit\s+note", text, re.IGNORECASE):
            raise PdfParseError("Πιστωτικό SALVADOR — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        head = HEAD_RE.search(text)
        if not head:
            raise PdfParseError("Λείπουν αριθμός/ημερομηνία SALVADOR")
        goods = amount_after(text, "Totale netto merce")
        rebate = amount_after(text, "Ulteriori sconti")
        net = amount_after(text, "Totale imponibile")
        vat = amount_after(text, "Totale imposta")
        total = amount_after(text, "Totale fattura")
        self.validate_total(net, vat, total)
        if vat != 0:
            raise PdfParseError(f"SALVADOR με ΦΠΑ {vat:.2f} — αναμένεται ενδοκοινοτική 0%")
        rebate_pct = (rebate * 100 / goods).quantize(Decimal("0.01")) if goods else Decimal("0")
        if abs(goods * rebate_pct / 100 - rebate) > Decimal("0.02"):
            raise PdfParseError(f"Έκπτωση SALVADOR {rebate:.2f} δεν είναι ενιαίο ποσοστό")
        rebate_pct = rebate_pct.normalize()

        lines: list[InvoiceLine] = []
        for match in LINE_RE.finditer(text):
            if match["vat"] != "INTR":
                raise PdfParseError(f"SALVADOR {match['code']}: ΦΠΑ {match['vat']} (όχι INTR)")
            if match["disc"]:
                raise PdfParseError(f"SALVADOR {match['code']}: έκπτωση γραμμής δεν υποστηρίζεται")
            qty = parse_amount(match["qty"])
            price = parse_amount(match["price"])
            amount = parse_amount(match["amount"])
            if abs(qty * price - amount) > Decimal("0.02"):
                raise PdfParseError(f"SALVADOR {match['code']}: {qty} x {price} != {amount}")
            value = (amount * (100 - rebate_pct) / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
            lines.append(
                InvoiceLine(
                    code=match["code"],
                    description=match["desc"].strip(),
                    quantity=qty,
                    unit_price=price,
                    discount_pct=rebate_pct,
                    value=value,
                    vat_pct=Decimal("0"),
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές SALVADOR")
        lines_sum = sum((line.value for line in lines), Decimal("0"))
        if abs(lines_sum - net) > Decimal("0.02"):
            raise PdfParseError(f"Άθροισμα γραμμών {lines_sum:.2f} != καθαρή αξία {net:.2f}")

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=head["number"],
            document_date=parse_date(head["date"]),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=f"SALVADOR FATTURA {head['number']}",
            raw_text=text,
            vat_pct=Decimal("0"),
            lines=tuple(lines),
        )
