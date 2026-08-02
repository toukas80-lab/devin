"""Parser for FedEx Express Greece invoices (VAT 095283423)."""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass

from pypdf import PdfReader

VAT_NUMBER = "095283423"
BLOCK_MARKER = "Αρ. Αποστολής"
SHIPMENT_RE = re.compile(r"\d{2}/\d{2}/\d{4}(\d{12})\b")
LEADING_AMOUNT_RE = re.compile(r"^-?[\d.,]+")
SUBTOTAL_RE = re.compile(r"Υπογραφή:\s*([\d.,]+)")
VAT_RATE_RE = re.compile(r"Ισχύον ΦΠΑ\s*([\d.,]+)\s*%")
INVOICE_NO_RE = re.compile(r"^\d{9}$", re.MULTILINE)
DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
TOTAL_RE = re.compile(r"Συνολική Αξία EUR\s*([\d.,]+)")
OWNER = "FOUNTOUKAS"


@dataclass
class Shipment:
    number: str
    amount: float
    vat_rate: float
    sender: str

    @property
    def is_export(self) -> bool:
        return OWNER in self.sender.upper()

    @property
    def vat(self) -> float:
        return round(self.amount * self.vat_rate / 100, 2)


@dataclass
class Invoice:
    number: str
    date: datetime.date
    due_date: datetime.date
    total: float
    shipments: list[Shipment]

    @property
    def net(self) -> float:
        return round(sum(s.amount for s in self.shipments), 2)

    @property
    def vat(self) -> float:
        # summing the rounded line amounts keeps the lines, the VAT analysis and
        # the document totals consistent to the cent
        return round(sum(s.vat for s in self.shipments), 2)


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def parse_pdf(path: str) -> Invoice:
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() for page in reader.pages)
    return parse_text(text)


def parse_text(text: str) -> Invoice:
    text = text.replace("\xa0", " ")
    header = text.split(BLOCK_MARKER)[0]
    dates = DATE_RE.findall(header)
    numbers = INVOICE_NO_RE.findall(header)
    if not numbers or len(dates) < 2:
        raise ValueError("could not read the FedEx invoice header")
    invoice_date = datetime.datetime.strptime(dates[0], "%d/%m/%Y").date()
    due_date = datetime.datetime.strptime(dates[1], "%d/%m/%Y").date()
    total_match = TOTAL_RE.search(text)
    if not total_match:
        raise ValueError("could not read the invoice total")

    shipments = []
    seen = set()
    for block in text.split(BLOCK_MARKER)[1:]:
        shipment = _parse_block(block)
        if shipment and shipment.number not in seen:
            seen.add(shipment.number)
            shipments.append(shipment)
    if not shipments:
        raise ValueError("no shipments found")

    return Invoice(
        number=numbers[0],
        date=invoice_date,
        due_date=due_date,
        total=_number(total_match.group(1)),
        shipments=shipments,
    )


def _parse_block(block: str) -> Shipment | None:
    number = SHIPMENT_RE.search(block)
    subtotal = SUBTOTAL_RE.search(block)
    if not number or not subtotal:
        return None
    rate = VAT_RATE_RE.search(block)
    return Shipment(
        number=number.group(1),
        amount=_number(subtotal.group(1)),
        vat_rate=_number(rate.group(1)) if rate else 0.0,
        sender=_sender(block),
    )


def _sender(block: str) -> str:
    lines = [line.strip() for line in block.splitlines()]
    for i, line in enumerate(lines):
        if "Αποστολέας" in line and i + 1 < len(lines):
            return LEADING_AMOUNT_RE.sub("", lines[i + 1]).strip()
    return ""
