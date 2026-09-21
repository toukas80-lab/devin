"""Build the DEVIN-EXP.txt / DEVIN-IMPORT.txt rows consumed by the SoftOne DImport script.

Expense (Ειδικές πιστωτών)  : date;series;creditor;docnum;account;netvalue;vat;comment
Purchase (Αγορές ειδών)     : date;series;supplier;docnum;item;qty;price;vat;disc
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from softone_pilot.config import AppConfig
from softone_pilot.models import InvoiceData, SupplierSettings

EXPENSE_FILE = "DEVIN-EXP.txt"
PURCHASE_FILE = "DEVIN-IMPORT.txt"
DOC_TYPE_PREFIX = re.compile(r"^[Α-ΩA-Z]{2,5}-")


@dataclass(frozen=True)
class TxtResult:
    expense_rows: tuple[str, ...]
    purchase_rows: tuple[str, ...]
    errors: tuple[str, ...]


def fmt(value: Decimal) -> str:
    text = f"{value:.2f}".replace(".", ",")
    return re.sub(r",?0+$", "", text) if "," in text else text


def docnum(invoice: InvoiceData) -> str:
    return DOC_TYPE_PREFIX.sub("", invoice.document_number.strip(), count=1)


def clean(text: str) -> str:
    return re.sub(r"[;\r\n]+", " ", text).strip()


def build_rows(invoice: InvoiceData, settings: SupplierSettings) -> tuple[str, list[str]]:
    date_text = invoice.document_date.strftime("%d/%m/%Y")
    number = docnum(invoice)
    vat = fmt(invoice.vat_pct)

    if settings.kind == "purchase":
        if not invoice.lines:
            raise ValueError("το PDF δεν έχει γραμμές ειδών για αγορά")
        rows = []
        for line in invoice.lines:
            item = settings.item_map.get(line.code)
            if not item:
                raise ValueError(f"χωρίς αντιστοίχιση είδους SoftOne ο κωδικός {line.code}")
            rows.append(
                ";".join(
                    (
                        date_text,
                        settings.series_code,
                        settings.trdr_code,
                        number,
                        item,
                        fmt(line.quantity),
                        fmt(line.unit_price),
                        vat,
                        fmt(line.discount_pct),
                    )
                )
            )
        return "purchase", rows

    comment = clean(f"{invoice.description} ({invoice.document_number})")
    row = ";".join(
        (
            date_text,
            settings.series_code,
            settings.trdr_code,
            number,
            settings.line_code,
            fmt(invoice.net_value),
            vat,
            comment,
        )
    )
    return "expense", [row]


def build_txt(invoices: list[InvoiceData], config: AppConfig) -> TxtResult:
    expense: list[str] = []
    purchase: list[str] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for invoice in invoices:
        name = invoice.source_path.name
        settings = config.suppliers.get(invoice.supplier_vat)
        if settings is None:
            errors.append(f"{name}: δεν υπάρχει ρύθμιση για ΑΦΜ {invoice.supplier_vat}")
            continue
        if not settings.trdr_code or not settings.series_code:
            errors.append(f"{name}: λείπει trdr_code ή series_code για {settings.name}")
            continue
        if settings.kind == "expense" and not settings.line_code:
            errors.append(f"{name}: λείπει line_code (λογαριασμός δαπάνης) για {settings.name}")
            continue
        key = (settings.trdr_code, docnum(invoice))
        if key in seen:
            errors.append(f"{name}: διπλό παραστατικό {key[1]} στο ίδιο batch")
            continue
        seen.add(key)
        try:
            kind, rows = build_rows(invoice, settings)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        (purchase if kind == "purchase" else expense).extend(rows)

    return TxtResult(tuple(expense), tuple(purchase), tuple(errors))


def write_txt(result: TxtResult, out_dir: str | Path) -> list[Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, rows in (
        (EXPENSE_FILE, result.expense_rows),
        (PURCHASE_FILE, result.purchase_rows),
    ):
        if not rows:
            continue
        path = target / filename
        path.write_text("\r\n".join(rows) + "\r\n", encoding="utf-8")
        written.append(path)
    return written
