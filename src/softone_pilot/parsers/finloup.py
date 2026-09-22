from __future__ import annotations

import re
from datetime import date
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

# Two layouts for the same monthly leasing invoice:
#  - Impact e-invoicing "ΤΠΥ 0000988" (Σχόλια "FINCO2-0988"), Greek amounts 54,16
#  - Stripe-style "Invoice-FINCO1-16086" (Τɩμολόγɩο with Latin iota ɩ), amounts "29,44 €"
# Both are numbered from the same FINCOn sequence, so the document number is the
# bare sequence number (FINCO2-0988 == ΤΠΥ 0000988 -> "988").

EINVOICE_ROW_RE = re.compile(
    r"(?P<qty>\d+,\d{2})Τεμάχια (?P<price>[\d.]+,\d{2}) (?P<disc_pct>[\d.]+,\d{2}) "
    r"(?P<disc>[\d.]+,\d{2}) (?P<net>[\d.]+,\d{2}) (?P<vat_pct>\d+) "
    r"(?P<vat>[\d.]+,\d{2}) (?P<total>[\d.]+,\d{2})"
)
EINVOICE_LINES_RE = re.compile(r"Τελικό\n(?P<body>.*?)\nΕκπτώσεις / Χρεώσεις", re.DOTALL)
STRIPE_ROW_RE = re.compile(
    r"^(?P<desc>[^\n]+)\n"
    r"(?P<from>\d{1,2} [Α-Ωα-ω]{3,4} \d{4}) (?P<to>\d{1,2} [Α-Ωα-ω]{3,4} \d{4})\n"
    r"(?P<qty>\d+) (?P<price>[\d.]+,\d{2}) € (?P<vat_pct>\d+)% (?P<net>[\d.]+,\d{2}) €",
    re.MULTILINE,
)
GREEK_MONTHS = {
    "ιανουαριου": 1,
    "φεβρουαριου": 2,
    "μαρτιου": 3,
    "απριλιου": 4,
    "μαιου": 5,
    "ιουνιου": 6,
    "ιουλιου": 7,
    "αυγουστου": 8,
    "σεπτεμβριου": 9,
    "οκτωβριου": 10,
    "νοεμβριου": 11,
    "δεκεμβριου": 12,
}
# The Stripe layout renders Greek iota as Latin "ɩ" (U+0269) and pads with NUL bytes.
IOTA_FIX = str.maketrans({"ɩ": "ι", "Ɩ": "Ι"})


def parse_greek_date(value: str) -> date:
    match = re.fullmatch(r"(\d{1,2}) ([Α-Ωα-ωίύόάέήώ]+) (\d{4})", value.strip())
    if not match:
        raise PdfParseError(f"Μη έγκυρη ημερομηνία FINLOUP: {value}")
    month = GREEK_MONTHS.get(greek_upper(match.group(2)).lower())
    if month is None:
        raise PdfParseError(f"Άγνωστος μήνας FINLOUP: {value}")
    return date(int(match.group(3)), month, int(match.group(1)))


class FinloupParser(SupplierParser):
    """Shared layouts; subclasses pin the AFM of each Finloup company."""

    def parse_text(self, source_path: Path, text: str) -> InvoiceData:
        text = re.sub(r"[ \t]+", " ", text.replace("\xa0", " ").replace("\x00", " "))
        text = text.translate(IOTA_FIX)
        if re.search(r"Πιστωτικό", text):
            raise PdfParseError("Πιστωτικό FINLOUP — δεν υποστηρίζεται, καταχώριση χειροκίνητα")
        if "Είδος Παραστατικού" in text:
            return self._parse_einvoice(source_path, text)
        if re.search(r"Αριθμός τιμολογίου FINCO\d", text):
            return self._parse_stripe(source_path, text)
        raise PdfParseError("Άγνωστη διάταξη FINLOUP")

    def _parse_einvoice(self, source_path: Path, text: str) -> InvoiceData:
        kind = first_match(text, (r"Είδος Παραστατικού\s*\n([^\n]+)",))
        if kind != "Τιμολόγιο Παροχής Υπηρεσιών":
            raise PdfParseError(f"Είδος παραστατικού FINLOUP «{kind}» — δεν υποστηρίζεται")
        number_text = first_match(text, (r"Αριθμός\s*\nΤΠΥ (\d+)\n",))
        date_text = first_match(text, (r"Ημερομηνία Έκδοσης\s*\n(\d{2}/\d{2}/\d{4})",))
        net_text = first_match(text, (r"Σύνολο Καθαρού Ποσού ([\d.]+,\d{2})",))
        vat_text = first_match(text, (r"Σύνολο Φ \. Π \. Α ([\d.]+,\d{2})",))
        total_text = first_match(text, (r"Συνολική Αξία ([\d.]+,\d{2})",))
        currency = first_match(text, (r"Νόμισμα (\w+)",))
        if not (number_text and date_text and net_text and vat_text and total_text):
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα FINLOUP")
        if currency != "EUR":
            raise PdfParseError(f"Νόμισμα FINLOUP {currency} — δεν υποστηρίζεται")

        body = EINVOICE_LINES_RE.search(text)
        if not body:
            raise PdfParseError("Δεν βρέθηκε ανάλυση γραμμών FINLOUP")
        lines: list[InvoiceLine] = []
        cursor = 0
        segment = body.group("body")
        for match in EINVOICE_ROW_RE.finditer(segment):
            raw = segment[cursor : match.start()]
            cursor = match.end()
            code = first_match(raw, (r"^\s*(\S+) ",)) or ""
            lines.append(
                InvoiceLine(
                    code=code,
                    description=clean_description(raw),
                    quantity=parse_amount(match["qty"]),
                    unit_price=parse_amount(match["price"]),
                    discount_pct=parse_amount(match["disc_pct"]),
                    value=parse_amount(match["net"]),
                    vat_pct=Decimal(match["vat_pct"]),
                )
            )
        return self._build(
            source_path,
            text,
            number_text,
            parse_date(date_text),
            parse_amount(net_text),
            parse_amount(vat_text),
            parse_amount(total_text),
            lines,
        )

    def _parse_stripe(self, source_path: Path, text: str) -> InvoiceData:
        number_text = first_match(text, (r"Αριθμός τιμολογίου FINCO\d+ (\d+)",))
        date_text = first_match(text, (r"Ημερομηνία έκδοσης (\d{1,2} [^\s]+ \d{4})",))
        net_text = first_match(text, (r"Σύνολο χωρίς φόρο ([\d.]+,\d{2}) €",))
        vat_text = first_match(
            text, (r"VAT - Greece\s+\d+% επί του ποσού [\d.]+,\d{2} €\s+([\d.]+,\d{2}) €",)
        )
        total_text = first_match(text, (r"\nΣύνολο ([\d.]+,\d{2}) €",))
        if not (number_text and date_text and net_text and vat_text and total_text):
            raise PdfParseError("Λείπουν αριθμός, ημερομηνία ή σύνολα FINLOUP")

        lines = [
            InvoiceLine(
                code=greek_upper(match["desc"]),
                description=(
                    f"ΜΙΣΘΩΜΑ {greek_upper(match['desc'])} "
                    f"({greek_upper(match['from'])} - {greek_upper(match['to'])})"
                ),
                quantity=Decimal(match["qty"]),
                unit_price=parse_amount(match["price"]),
                discount_pct=Decimal("0"),
                value=parse_amount(match["net"]),
                vat_pct=Decimal(match["vat_pct"]),
            )
            for match in STRIPE_ROW_RE.finditer(text)
        ]
        return self._build(
            source_path,
            text,
            number_text,
            parse_greek_date(date_text),
            parse_amount(net_text),
            parse_amount(vat_text),
            parse_amount(total_text),
            lines,
        )

    def _build(
        self,
        source_path: Path,
        text: str,
        number_text: str,
        document_date: date,
        net: Decimal,
        vat: Decimal,
        total: Decimal,
        lines: list[InvoiceLine],
    ) -> InvoiceData:
        if not lines:
            raise PdfParseError("Δεν βρέθηκαν γραμμές FINLOUP")
        self.validate_total(net, vat, total)
        lines_net = sum((line.value for line in lines), Decimal("0"))
        if lines_net != net:
            raise PdfParseError(
                f"Οι γραμμές FINLOUP ({lines_net:.2f}) δεν συμφωνούν με την καθαρή αξία {net:.2f}"
            )
        vat_pct = self.uniform_vat_pct(net, vat)
        if any(line.vat_pct != vat_pct for line in lines):
            raise PdfParseError("Μεικτός ΦΠΑ FINLOUP — καταχώριση χειροκίνητα")
        return InvoiceData(
            source_path=source_path,
            supplier_name=self.name,
            supplier_vat=self.vat,
            document_number=number_text.lstrip("0") or "0",
            document_date=document_date,
            net_value=net,
            vat_value=vat,
            total_value=total,
            description=" - ".join(line.description for line in lines),
            raw_text=text,
            vat_pct=vat_pct,
            lines=tuple(lines),
        )


def clean_description(raw: str) -> str:
    text = greek_upper(raw.replace("\n", " "))
    text = re.sub(r"^\S+ \d+ - FIXED \d+ - 1 X ", "", text)
    return "ΜΙΣΘΩΜΑ " + re.sub(r"\s*\(AT €[\d.]+ / MONTH\)$", "", text).strip()


class FinloupLeasing2Parser(FinloupParser):
    vat = "803183981"
    name = "FINLOUP LEASING II ΜΟΝΟΠΡΟΣΩΠΗ Α.Ε."


class FinloupLeasing1Parser(FinloupParser):
    vat = "802285336"
    name = "FINLOUP LEASING I Α.Ε."
