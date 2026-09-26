from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, InvoiceLine
from softone_pilot.parsers.base import (
    VAT_RATES,
    PdfParseError,
    SupplierParser,
    first_match,
    greek_upper,
    parse_amount,
    parse_date,
)

# Charge line, pct glued to net: "24380,00 471,20ΝΑΥΛΟΣ / FREIGHT 91,20"
CHARGE_RE = re.compile(
    r"^(?P<pctnet>\d+(?:\.\d{3})*,\d{2}) (?P<total>[\d.]+,\d{2})"
    r"(?P<desc>[^\d\n][^\n]*?) (?P<vat>[\d.]+,\d{2})$",
    re.MULTILINE,
)


def split_pct_net(pctnet: str, vat: Decimal, total: Decimal) -> tuple[Decimal, Decimal]:
    for pct in VAT_RATES:
        prefix = str(int(pct))
        if not pctnet.startswith(prefix) or len(pctnet) <= len(prefix):
            continue
        net = parse_amount(pctnet[len(prefix) :])
        if abs(net * pct / 100 - vat) <= Decimal("0.02") and abs(net + vat - total) <= Decimal(
            "0.02"
        ):
            return pct, net
    raise PdfParseError(f"Μη αναγνωρίσιμη γραμμή χρέωσης ΚΑΡΑΣΟΥΛΗΣ: {pctnet}")


class KarasoulisParser(SupplierParser):
    vat = "094453479"
    name = "ΚΑΡΑΣΟΥΛΗΣ Α.Ε"

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        if re.search(r"Πιστωτικό|ΠΤΠΥ-", text):
            raise PdfParseError("Πιστωτικό ΚΑΡΑΣΟΥΛΗΣ — δεν υποστηρίζεται, καταχώριση χειροκίνητα")

        number_text = first_match(text, (r"\bΤΠΥ-(\d+)\b",))
        date_text = first_match(text, (r"Τιμολόγιο Παροχής Υπηρεσιών\s+(\d{1,2}/\d{1,2}/\d{4})",))
        if not number_text or not date_text:
            raise PdfParseError("Λείπουν αριθμός ή ημερομηνία ΚΑΡΑΣΟΥΛΗΣ")

        sender = first_match(text, (r"\nΕΛΛΑΔΑ\n([^\n]+)\n[^\n]+\n([^\n]+)\n",))
        origin = re.search(r"\nΕΛΛΑΔΑ\n[^\n]+\n[^\n]+\n([^\n]+)\n", text)
        cargo = " ".join(
            part
            for part in (
                greek_upper(sender) if sender else "",
                f"({greek_upper(origin.group(1))})" if origin else "",
            )
            if part
        )

        lines: list[InvoiceLine] = []
        for match in CHARGE_RE.finditer(text):
            vat = parse_amount(match["vat"])
            total = parse_amount(match["total"])
            pct, net = split_pct_net(match["pctnet"], vat, total)
            desc = greek_upper(match["desc"].split("/")[0])
            lines.append(
                InvoiceLine(
                    code=desc,
                    description=f"{desc} {cargo}".strip(),
                    quantity=Decimal("1"),
                    unit_price=net,
                    discount_pct=Decimal("0"),
                    value=net,
                    vat_pct=pct,
                )
            )
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές χρέωσης ΚΑΡΑΣΟΥΛΗΣ")

        net = sum((line.value for line in lines), Decimal("0"))
        vat = sum(
            ((line.value * line.vat_pct / 100).quantize(Decimal("0.01")) for line in lines),
            Decimal("0"),
        )
        total = net + vat
        if not re.search(rf"^{re.escape(fmt_el(total))}$", text, re.MULTILINE):
            raise PdfParseError(f"Το σύνολο {total:.2f} δεν επιβεβαιώνεται στο PDF ΚΑΡΑΣΟΥΛΗΣ")

        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number_text.lstrip("0") or "0",
            document_date=parse_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=lines[0].description,
            raw_text=text,
            vat_pct=lines[0].vat_pct,
            lines=tuple(lines),
        )


def fmt_el(value: Decimal) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
