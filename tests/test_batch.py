from datetime import date
from decimal import Decimal
from pathlib import Path

import softone_pilot.batch as batch
from softone_pilot.automation import SoftOneLaunch, WorkflowExecution
from softone_pilot.config import AppConfig, AutomationSettings, SqlSettings
from softone_pilot.models import (
    InvoiceData,
    PreparedInvoice,
    SqlSupplier,
    SupplierSettings,
)


def prepared_invoice(path: Path) -> PreparedInvoice:
    return PreparedInvoice(
        invoice=InvoiceData(
            source_path=path,
            supplier_name="Supplier",
            supplier_vat="123456789",
            document_number="INV-1",
            document_date=date(2026, 7, 11),
            net_value=Decimal("100.00"),
            vat_value=Decimal("24.00"),
            total_value=Decimal("124.00"),
            description="Service",
            raw_text="private",
        ),
        settings=SupplierSettings(
            name="Supplier",
            series_code="ΤΙΜΔ",
            line_code="18103",
            payment_method="1008",
            settlement=False,
        ),
        sql_supplier=SqlSupplier(
            trdr_id=1,
            code="0077",
            name="Supplier",
            vat="123456789",
            payment="1008",
        ),
        duplicate=None,
        errors=(),
        warnings=(),
    )


def app_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        sql=SqlSettings(
            enabled=False,
            server=r".\SOFTONE",
            database="FOUNTOUKAS",
            driver="ODBC Driver 17 for SQL Server",
            trusted_connection=True,
            timeout_seconds=10,
        ),
        automation=AutomationSettings(
            enabled=True,
            executable_path="SoftOne.exe",
            arguments=(),
            inbox_path=str(tmp_path / "inbox"),
            processed_path=str(tmp_path / "processed"),
            failed_path=str(tmp_path / "failed"),
            startup_timeout_seconds=60,
            credential_target="SoftOne PDF Pilot",
            startup_profile="softone.login",
            navigation_profile="creditor_expense.open_create",
        ),
        suppliers={},
    )


def test_no_save_batch_stops_after_first_pdf(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "invoice.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr(
        batch,
        "launch_softone",
        lambda *args, **kwargs: SoftOneLaunch(launched=True, process_id=42),
    )
    monkeypatch.setattr(batch, "_credential_context", lambda target: {})

    def execute(profile, name, context, **kwargs):
        return WorkflowExecution(
            profile=name,
            executed_steps=("filled",),
            save_skipped=name == "creditor_expense.create",
        )

    monkeypatch.setattr(batch, "execute_profile", execute)
    result = batch.execute_batch(
        [prepared_invoice(source)],
        app_config(tmp_path),
        "workflow.json",
    )

    assert result.stopped_early
    assert not result.results[0].saved
    assert result.results[0].save_skipped
    assert source.exists()


def test_saved_pdf_moves_to_processed(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "invoice.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr(
        batch,
        "launch_softone",
        lambda *args, **kwargs: SoftOneLaunch(launched=False),
    )
    monkeypatch.setattr(batch, "_credential_context", lambda target: {})
    monkeypatch.setattr(
        batch,
        "execute_profile",
        lambda profile, name, context, **kwargs: WorkflowExecution(
            profile=name,
            executed_steps=("saved",),
            save_skipped=False,
            saved=True,
        ),
    )

    result = batch.execute_batch(
        [prepared_invoice(source)],
        app_config(tmp_path),
        "workflow.json",
        allow_save=True,
    )

    assert result.results[0].saved
    assert not result.results[0].save_skipped
    assert (tmp_path / "processed" / "invoice.pdf").exists()
    assert not source.exists()


def test_allow_save_without_executed_save_keeps_pdf(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "invoice.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr(
        batch,
        "launch_softone",
        lambda *args, **kwargs: SoftOneLaunch(launched=False),
    )
    monkeypatch.setattr(batch, "_credential_context", lambda target: {})
    monkeypatch.setattr(
        batch,
        "execute_profile",
        lambda profile, name, context, **kwargs: WorkflowExecution(
            profile=name,
            executed_steps=("filled",),
            save_skipped=False,
            saved=False,
        ),
    )

    result = batch.execute_batch(
        [prepared_invoice(source)],
        app_config(tmp_path),
        "workflow.json",
        allow_save=True,
    )

    assert not result.results[0].saved
    assert source.exists()
