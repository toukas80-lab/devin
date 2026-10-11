"""USD -> EUR conversion with the ECB reference rate of the invoice date."""

from __future__ import annotations

import re
import urllib.request
from collections.abc import Callable
from dataclasses import replace
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from xml.etree import ElementTree

from softone_pilot.models import InvoiceData

ECB_90D_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
ECB_HIST_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
MAX_RATE_AGE = timedelta(days=7)
CENT = Decimal("0.01")
RATE_PLACES = Decimal("0.0001")


class FxError(ValueError):
    pass


class RateTooOld(FxError):
    """The requested day precedes the downloaded ECB window."""


def parse_ecb_usd_rates(xml_text: str) -> dict[date, Decimal]:
    """Return {day: USD per 1 EUR} from an ECB eurofxref XML document."""
    rates: dict[date, Decimal] = {}
    for cube in ElementTree.fromstring(xml_text).iter():
        day_text = cube.attrib.get("time")
        if not day_text:
            continue
        day = date.fromisoformat(day_text)
        for child in cube:
            if child.attrib.get("currency") == "USD":
                rates[day] = Decimal(child.attrib["rate"])
    if not rates:
        raise FxError("Δεν βρέθηκε ισοτιμία USD στα δεδομένα της ΕΚΤ")
    return rates


def eur_per_usd(rates: dict[date, Decimal], day: date) -> Decimal:
    """ECB reference rate valid on `day` (last published on or before it), as EUR per 1 USD."""
    candidates = [d for d in rates if d <= day]
    if not candidates:
        raise RateTooOld(f"Δεν υπάρχει ισοτιμία ΕΚΤ για {day:%d/%m/%Y} ή νωρίτερα")
    latest = max(candidates)
    if day - latest > MAX_RATE_AGE:
        raise FxError(
            f"Η τελευταία ισοτιμία ΕΚΤ ({latest:%d/%m/%Y}) είναι πολύ παλιά για {day:%d/%m/%Y}"
        )
    return (Decimal("1") / rates[latest]).quantize(RATE_PLACES, rounding=ROUND_HALF_UP)


def fetch_ecb_usd_rates(url: str = ECB_90D_URL) -> dict[date, Decimal]:
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return parse_ecb_usd_rates(response.read().decode("utf-8"))
    except OSError as exc:
        raise FxError(f"Αποτυχία λήψης ισοτιμιών ΕΚΤ: {exc}") from exc


def parse_rate(text: str) -> Decimal:
    normalized = text.strip().replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d+)?", normalized) or Decimal(normalized) <= 0:
        raise FxError(f"Μη έγκυρη ισοτιμία: {text}")
    return Decimal(normalized)


def rate_resolver(rate_text: str | None) -> Callable[[date], Decimal]:
    """Fixed `--rate` (EUR per 1 USD) if given, else the ECB reference rate per invoice date."""
    if rate_text:
        fixed = parse_rate(rate_text)
        return lambda _day: fixed
    return EcbResolver()


class EcbResolver:
    """Uses the 90-day ECB feed; downloads the full history (8 MB) only for older invoices."""

    def __init__(self) -> None:
        self.rates = fetch_ecb_usd_rates(ECB_90D_URL)
        self.full_history = False

    def __call__(self, day: date) -> Decimal:
        try:
            return eur_per_usd(self.rates, day)
        except RateTooOld:
            if self.full_history:
                raise
            self.rates = fetch_ecb_usd_rates(ECB_HIST_URL)
            self.full_history = True
            return eur_per_usd(self.rates, day)


def convert_invoices(
    invoices: list[InvoiceData], rate_text: str | None, errors: list[str]
) -> list[InvoiceData]:
    """EUR invoices pass through; foreign ones are converted or dropped with an error."""
    foreign = [invoice for invoice in invoices if invoice.currency != "EUR"]
    if not foreign:
        return invoices

    try:
        rate_for = rate_resolver(rate_text)
    except FxError as exc:
        errors.extend(f"{invoice.source_path.name}: {exc}" for invoice in foreign)
        return [invoice for invoice in invoices if invoice.currency == "EUR"]

    converted: list[InvoiceData] = []
    for invoice in invoices:
        try:
            converted.append(convert_to_eur(invoice, rate_for(invoice.document_date)))
        except FxError as exc:
            errors.append(f"{invoice.source_path.name}: {exc}")
    return converted


def to_eur(amount: Decimal, rate: Decimal) -> Decimal:
    return (amount * rate).quantize(CENT, rounding=ROUND_HALF_UP)


def convert_to_eur(invoice: InvoiceData, rate: Decimal) -> InvoiceData:
    """Convert a USD invoice to EUR at `rate` (EUR per 1 USD); the comment keeps the audit trail."""
    if invoice.currency == "EUR":
        return invoice
    if invoice.currency != "USD":
        raise FxError(f"Μη υποστηριζόμενο νόμισμα {invoice.currency}")

    def tag(amount: Decimal) -> str:
        return f"${amount:.2f} X {rate}".replace(".", ",")

    lines = tuple(
        replace(
            line,
            unit_price=to_eur(line.unit_price, rate),
            value=to_eur(line.value, rate),
            description=f"{line.description} {tag(line.value)}",
        )
        for line in invoice.lines
    )
    net = to_eur(invoice.net_value, rate)
    vat = to_eur(invoice.vat_value, rate)
    total = to_eur(invoice.total_value, rate)
    if abs(net + vat - total) > CENT * 2:
        raise FxError(f"Ασυμφωνία μετά τη μετατροπή: {net} + {vat} != {total}")
    return replace(
        invoice,
        currency="EUR",
        net_value=net,
        vat_value=vat,
        total_value=net + vat,
        description=f"{invoice.description} {tag(invoice.total_value)}",
        lines=lines,
    )
