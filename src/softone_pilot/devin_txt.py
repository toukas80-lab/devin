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
# written by DevinExpMakeHead / DevinMakeHead for the ASCII wizard, which re-creates whatever
# they contain: a stale one must never survive a new run
HEAD_FILES = ("DEVIN-EXPHEAD.txt", "DEVIN-HEAD.txt")
# Greek document-type prefixes (ΤΠΥ-, ΑΠΥ-, ...) and INV- are dropped; Latin prefixes that are
# part of the supplier's numbering (SIB-, ZZCYINBS-) stay, matching the historical FINCODEs.
DOC_TYPE_PREFIX = re.compile(r"^(?:[Α-Ω]{2,5}|INV)-")


@dataclass(frozen=True)
class TxtResult:
    expense_rows: tuple[str, ...]
    purchase_rows: tuple[str, ...]
    errors: tuple[str, ...]
    done: tuple[Path, ...] = ()
    """Source PDFs whose rows made it into the output."""


def fmt(value: Decimal) -> str:
    text = f"{value:.2f}".replace(".", ",")
    return re.sub(r",?0+$", "", text) if "," in text else text


def fmt_vat(pct: Decimal, vat_ids: dict[str, str]) -> str:
    """`ID:n` when the percent is mapped to a SoftOne VAT id (e.g. 0% is ambiguous), else the %."""
    vat_id = vat_ids.get(fmt(pct))
    return f"ID:{vat_id}" if vat_id else fmt(pct)


def docnum(invoice: InvoiceData) -> str:
    return DOC_TYPE_PREFIX.sub("", invoice.document_number.strip(), count=1)


def clean(text: str) -> str:
    return re.sub(r"[;\r\n]+", " ", text).strip()


def build_rows(
    invoice: InvoiceData, settings: SupplierSettings, vat_ids: dict[str, str] | None = None
) -> tuple[str, list[str]]:
    date_text = invoice.document_date.strftime("%d/%m/%Y")
    number = docnum(invoice)
    vat_ids = vat_ids or {}

    if settings.kind == "purchase":
        if not invoice.lines:
            raise ValueError("το PDF δεν έχει γραμμές ειδών για αγορά")
        rows = []
        for line in invoice.lines:
            item = settings.item_map.get(line.code)
            if not item:
                raise ValueError(
                    f'χωρίς κωδικό είδους SoftOne — πρόσθεσε στο item_map: "{line.code}": "..."'
                )
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
                        fmt_vat(line.vat_pct, vat_ids),
                        fmt(line.discount_pct),
                    )
                )
            )
        return "purchase", rows

    head = (date_text, settings.series_code, settings.trdr_code, number)
    if invoice.lines:
        rows = [
            ";".join(
                (
                    *head,
                    settings.expense_account(line),
                    fmt(line.value),
                    fmt_vat(line.vat_pct, vat_ids),
                    clean(f"{line.description} ({invoice.document_number})"),
                )
            )
            for line in invoice.lines
        ]
        return "expense", rows

    if not settings.line_code:
        raise ValueError("λείπει line_code (λογαριασμός δαπάνης)")
    comment = clean(f"{invoice.description} ({invoice.document_number})")
    row = ";".join(
        (
            *head,
            settings.line_code,
            fmt(invoice.net_value),
            fmt_vat(invoice.vat_pct, vat_ids),
            comment,
        )
    )
    return "expense", [row]


def build_txt(invoices: list[InvoiceData], config: AppConfig) -> TxtResult:
    expense: list[str] = []
    purchase: list[str] = []
    errors: list[str] = []
    done: list[Path] = []
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
        if settings.kind == "expense" and not settings.has_expense_account:
            errors.append(f"{name}: λείπει line_code (λογαριασμός δαπάνης) για {settings.name}")
            continue
        key = (settings.trdr_code, docnum(invoice))
        if key in seen:
            errors.append(f"{name}: διπλό παραστατικό {key[1]} στο ίδιο batch")
            continue
        seen.add(key)
        try:
            kind, rows = build_rows(invoice, settings, config.vat_ids)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        (purchase if kind == "purchase" else expense).extend(rows)
        done.append(invoice.source_path)

    return TxtResult(tuple(expense), tuple(purchase), tuple(errors), tuple(done))


def row_key(row: str) -> tuple[str, str]:
    """(trdr, docnum) - the pair the DImport script uses to recognise an existing document."""
    fields = row.split(";")
    return (fields[2], fields[3]) if len(fields) >= 4 else (row, "")


def read_rows(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [row for row in path.read_text(encoding="utf-8").splitlines() if row.strip()]


def merge_rows(existing: list[str], new: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """Rows of a previous run stay in the file (the SoftOne side SKIPs what already exists);
    a document that appears again replaces its old rows. Returns (kept old rows, merged)."""
    new_keys = {row_key(row) for row in new}
    kept = [row for row in existing if row_key(row) not in new_keys]
    return kept, kept + list(new)


@dataclass(frozen=True)
class WrittenFile:
    path: Path
    new_rows: int
    kept_rows: int


def write_txt(result: TxtResult, out_dir: str | Path) -> list[WrittenFile]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    for head in HEAD_FILES:
        (target / head).unlink(missing_ok=True)
    written: list[WrittenFile] = []
    for filename, rows in (
        (EXPENSE_FILE, result.expense_rows),
        (PURCHASE_FILE, result.purchase_rows),
    ):
        path = target / filename
        kept, merged = merge_rows(read_rows(path), rows)
        if not merged:
            path.unlink(missing_ok=True)
            continue
        path.write_text("\r\n".join(merged) + "\r\n", encoding="utf-8")
        written.append(WrittenFile(path, len(rows), len(kept)))
    return written
