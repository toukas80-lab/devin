from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from softone_pilot.config import AppConfig
from softone_pilot.models import PreparedInvoice
from softone_pilot.parsers import parse_pdf
from softone_pilot.parsers.base import PdfParseError
from softone_pilot.sql_readonly import SoftOneReadOnlyRepository, SqlReadOnlyError
from softone_pilot.validation import validate_invoice


def collect_pdfs(path: str | Path) -> list[Path]:
    source = Path(path)
    if source.is_file():
        return [source] if source.suffix.lower() == ".pdf" else []
    if source.is_dir():
        return sorted(item for item in source.iterdir() if item.suffix.lower() == ".pdf")
    return []


def prepare_batch(
    pdf_paths: Iterable[Path],
    config: AppConfig,
    use_sql: bool,
) -> tuple[list[PreparedInvoice], list[str]]:
    invoices = []
    parse_errors: list[str] = []

    for path in pdf_paths:
        try:
            invoices.append(parse_pdf(path))
        except PdfParseError as exc:
            parse_errors.append(f"{path.name}: {exc}")

    prepared: list[PreparedInvoice] = []
    if use_sql and config.sql.enabled:
        try:
            with SoftOneReadOnlyRepository(config.sql) as repository:
                for invoice in invoices:
                    prepared.append(_prepare(invoice, config, repository))
        except SqlReadOnlyError as exc:
            parse_errors.append(str(exc))
            prepared.extend(_prepare(invoice, config, None) for invoice in invoices)
    else:
        prepared.extend(_prepare(invoice, config, None) for invoice in invoices)

    return prepared, parse_errors


def _prepare(invoice, config, repository) -> PreparedInvoice:
    settings = config.suppliers.get(invoice.supplier_vat)
    errors, warnings = validate_invoice(invoice, settings)
    sql_supplier = None
    duplicate = None

    if repository is not None:
        sql_supplier = repository.find_supplier(invoice.supplier_vat)
        if sql_supplier is None:
            errors.append(f"Δεν βρέθηκε ενεργός προμηθευτής SQL για ΑΦΜ {invoice.supplier_vat}")
        duplicate = repository.find_duplicate(
            invoice.supplier_vat,
            invoice.document_number,
            invoice.document_date,
        )
        if duplicate is not None:
            errors.append(f"Πιθανό διπλότυπο SoftOne FINDOC={duplicate.findoc_id}")
    else:
        warnings.append("Ο SQL έλεγχος προμηθευτή/διπλοτύπου δεν εκτελέστηκε")

    return PreparedInvoice(
        invoice=invoice,
        settings=settings,
        sql_supplier=sql_supplier,
        duplicate=duplicate,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def dry_run_steps(item: PreparedInvoice) -> list[str]:
    invoice = item.invoice
    settings = item.settings
    supplier_code = item.sql_supplier.code if item.sql_supplier else "<SQL lookup>"
    return [
        "Έλεγχος ότι είναι ενεργή η σωστή φόρμα παραστατικού αγοράς",
        f"Νέο παραστατικό για προμηθευτή {supplier_code}",
        f"Σειρά: {settings.series_code if settings else '<λείπει>'}",
        f"Ημερομηνία: {invoice.document_date.strftime('%d/%m/%Y')}",
        f"Αριθμός: {invoice.document_number}",
        f"Αιτιολογία: {invoice.description}",
        f"Κωδικός γραμμής: {settings.line_code if settings else '<λείπει>'}",
        f"Καθαρή αξία: {invoice.net_value:.2f}",
        f"ΦΠΑ: {invoice.vat_value:.2f}",
        f"Σύνολο: {invoice.total_value:.2f}",
        f"Τρόπος πληρωμής: {settings.payment_method if settings else '<λείπει>'}",
        "Αναμονή επιβεβαίωσης αποθήκευσης πριν από το επόμενο PDF",
    ]
