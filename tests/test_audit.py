import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from softone_pilot.audit import write_batch_audit, write_dry_run_audit
from softone_pilot.batch import BatchExecution, BatchItemResult
from softone_pilot.models import InvoiceData, PreparedInvoice


def test_write_dry_run_audit_excludes_raw_pdf_text(tmp_path: Path) -> None:
    invoice = InvoiceData(
        source_path=Path("invoice.pdf"),
        supplier_name="Supplier",
        supplier_vat="123456789",
        document_number="INV-1",
        document_date=date(2026, 7, 1),
        net_value=Decimal("100.00"),
        vat_value=Decimal("24.00"),
        total_value=Decimal("124.00"),
        description="Service",
        raw_text="CONFIDENTIAL PDF CONTENT",
    )
    item = PreparedInvoice(
        invoice=invoice,
        settings=None,
        sql_supplier=None,
        duplicate=None,
        errors=("Missing mapping",),
        warnings=(),
    )
    target = write_dry_run_audit(tmp_path / "audit.jsonl", [item], [])

    content = target.read_text(encoding="utf-8")
    event = json.loads(content)
    assert event["summary"]["blocked"] == 1
    assert "CONFIDENTIAL" not in content


def test_write_batch_audit_contains_no_credentials(tmp_path: Path) -> None:
    result = BatchExecution(
        launched=True,
        results=(
            BatchItemResult(
                source_path=Path("invoice.pdf"),
                profile="creditor_expense.create",
                executed_steps=("supplier", "save"),
                saved=True,
                save_skipped=False,
            ),
        ),
        stopped_early=False,
    )
    target = write_batch_audit(tmp_path / "batch.jsonl", result)

    event = json.loads(target.read_text(encoding="utf-8"))
    assert event["items"][0]["saved"]
    assert not event["items"][0]["save_skipped"]
    assert "password" not in target.read_text(encoding="utf-8").lower()
