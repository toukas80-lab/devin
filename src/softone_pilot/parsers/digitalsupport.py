from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData
from softone_pilot.parsers.base import (
    PdfParseError,
    SupplierParser,
    first_match,
    parse_amount,
    parse_date,
)

# "3,00ΏρεςLH 40,00 0,00 0,00 120,00 0,00 24 28,80148,80"
#  qty  unit  price  disc% disc  net  disc-total vat%  vat-amount+total (glued)
LINE_RE = re.compile(
    r"(?P<qty>\d+,\d{2})Ώρες\S* (?P<price>[\d.]+,\d{2}) [\d.,]+ [\d.,]+ (?P<net>[\d.]+,\d{2}) "
    r"[\d.,]+ (?P<vat>\d{1,2}) [\d.]+,\d{2}\s*[\d.]+,\d{2}\s*\nΣχόλια (?P<note>[^\n]+)"
)


class DigitalSupportParser(SupplierParser):
    """DIGITAL SUPPORT (ΚΑΠΕΤΑΝΑΚΗ ΚΑΜΠΟΥΡΗΣ Ε.Ε.) IT-support invoice from the Impact e-invoicing
    portal: hourly lines with the same account/VAT, summarised into one expense row."""

    vat = "802175958"
    name = "ΚΑΠΕΤΑΝΑΚΗ ΚΑΜΠΟΥΡΗΣ Ε.Ε. (DIGITAL SUPPORT)"

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = re.sub(r"[ \t]+", " ", text.replace("\xa0", " "))
        if re.search(r"Πιστωτικό", text, re.IGNORECASE):
            raise PdfParseError(
                "Πιστωτικό DIGITAL SUPPORT — δεν υποστηρίζεται, καταχώριση χειροκίνητα"
            )
        number = first_match(text, (r"Αριθμός\s*\nΤΠΥ (\d+)",))
        date_text = first_match(text, (r"Ημερομηνία Έκδοσης\s*\n(\d{2}/\d{2}/\d{4})",))
        net_text = first_match(text, (r"Σύνολο Καθαρού Ποσού (\d[\d.]*,\d{2})",))
        vat_text = first_match(text, (r"Σύνολο Φ ?\. ?Π ?\. ?Α (\d[\d.]*,\d{2})",))
        total_text = first_match(text, (r"Συνολική Αξία (\d[\d.]*,\d{2})",))
        if not all((number, date_text, net_text, vat_text, total_text)):
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα DIGITAL SUPPORT")
        assert number and date_text and net_text and vat_text and total_text
        net, vat, total = parse_amount(net_text), parse_amount(vat_text), parse_amount(total_text)
        self.validate_total(net, vat, total)
        vat_pct = self.uniform_vat_pct(net, vat)

        hours = Decimal("0")
        lines_net = Decimal("0")
        notes: list[str] = []
        for match in LINE_RE.finditer(text):
            if Decimal(match["vat"]) != vat_pct:
                raise PdfParseError(
                    f"Γραμμή DIGITAL SUPPORT με ΦΠΑ {match['vat']}% (αναμενόταν {vat_pct}%)"
                )
            hours += parse_amount(match["qty"])
            lines_net += parse_amount(match["net"])
            notes.append(match["note"].strip())
        if not notes:
            raise PdfParseError("Δεν βρέθηκαν γραμμές υπηρεσιών DIGITAL SUPPORT")
        if abs(lines_net - net) > Decimal("0.02"):
            raise PdfParseError(f"Το σύνολο γραμμών {lines_net:.2f} != καθαρή αξία {net:.2f}")

        hours_text = f"{hours:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        description = f"ΤΕΧΝΙΚΗ ΥΠΟΣΤΗΡΙΞΗ {hours_text} ΩΡΕΣ - {', '.join(notes)}"
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number.lstrip("0"),
            document_date=parse_date(date_text),
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=description,
            raw_text=text,
            vat_pct=vat_pct,
        )
