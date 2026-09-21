"""Drop-folder batch: read every PDF in <base>\\PDF, write DEVIN-EXP.txt / DEVIN-IMPORT.txt
next to it and move the processed PDFs to PDF\\ΕΓΙΝΑΝ\\<date>. UI lives in dropfolder_app."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from softone_pilot.config import AppConfig, load_config
from softone_pilot.devin_txt import build_txt, write_txt
from softone_pilot.fx import convert_invoices
from softone_pilot.models import InvoiceData
from softone_pilot.parsers import parse_pdf
from softone_pilot.parsers.base import PdfParseError
from softone_pilot.planner import collect_pdfs

DEFAULT_BASE = Path(r"C:\Soft1")
PDF_DIR = "PDF"
DONE_DIR = "ΕΓΙΝΑΝ"
CONFIG_FILE = "devin-config.json"
INSTALLED_DEFAULT_FILE = "devin-config.default.json"
REPORT_FILE = "DEVIN-REPORT.txt"
DEFAULT_CONFIG = Path(__file__).with_name("devin-config.default.json")


def ensure_config(base: Path, report: list[str]) -> AppConfig:
    """Load base/devin-config.json.

    The bundled default is copied on first run and kept as devin-config.default.json.
    A newer .exe replaces a config that still equals the previously installed default
    (or predates that marker file); a hand-edited one is kept with a warning.
    """
    target = base / CONFIG_FILE
    installed = base / INSTALLED_DEFAULT_FILE
    bundled = DEFAULT_CONFIG.read_bytes()
    unedited = not installed.exists() or installed.read_bytes() == target.read_bytes()
    if not target.exists() or unedited:
        target.write_bytes(bundled)
    elif installed.read_bytes() != bundled:
        report.append(
            f"ΠΡΟΣΟΧΗ: το {target} έχει αλλαχθεί χειροκίνητα και δεν ενημερώθηκε — "
            f"οι νέες ρυθμίσεις είναι στο {installed}"
        )
    installed.write_bytes(bundled)
    return load_config(target)


def run(base: Path) -> list[str]:
    report: list[str] = []
    pdf_dir = base / PDF_DIR
    pdf_dir.mkdir(parents=True, exist_ok=True)
    config = ensure_config(base, report)

    pdfs = collect_pdfs(pdf_dir)
    if not pdfs:
        report.append(f"Δεν βρέθηκαν PDF στο {pdf_dir} — τα υπάρχοντα DEVIN-*.txt δεν αλλάζουν")
        return report

    invoices: list[InvoiceData] = []
    errors: list[str] = []
    for path in pdfs:
        try:
            invoices.append(parse_pdf(path))
        except PdfParseError as exc:
            errors.append(f"{path.name}: {exc}")

    invoices = convert_invoices(invoices, None, errors)
    result = build_txt(invoices, config)
    errors.extend(result.errors)
    written = write_txt(result, base)

    done_dir = pdf_dir / DONE_DIR / f"{date.today():%Y-%m-%d}"
    for source in result.done:
        done_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(done_dir / source.name))

    report.append(f"PDF: {len(pdfs)}   ΟΚ: {len(result.done)}   ΠΡΟΒΛΗΜΑ: {len(errors)}")
    report.append("")
    if result.expense_rows:
        report.append(f"ΔΑΠΑΝΕΣ -> DEVIN-EXP.txt ({len(result.expense_rows)} γραμμές)")
        report.extend(f"  {row}" for row in result.expense_rows)
        report.append("")
    if result.purchase_rows:
        report.append(f"ΑΓΟΡΕΣ -> DEVIN-IMPORT.txt ({len(result.purchase_rows)} γραμμές)")
        report.extend(f"  {row}" for row in result.purchase_rows)
        report.append("")
    if errors:
        report.append("ΔΕΝ ΠΕΡΑΣΑΝ (μένουν στον φάκελο PDF):")
        report.extend(f"  {error}" for error in errors)
        report.append("")
    if result.done:
        report.append(f"Τα {len(result.done)} PDF μεταφέρθηκαν στο {done_dir}")
    if written:
        report.append("Επόμενο στη SoftOne: DevinExpMakeHead / DevinMakeHead -> Import -> AddLines")
    else:
        report.append("Δεν γράφτηκε κανένα αρχείο για τη SoftOne")
    return report
