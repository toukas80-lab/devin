from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from softone_pilot.automation import (
    SoftOneAutomationError,
    build_invoice_context,
    commit_is_available,
    preview_workflow,
    validate_workflow_profile,
)
from softone_pilot.models import (
    InvoiceData,
    PreparedInvoice,
    SqlSupplier,
    SupplierSettings,
)

WORKFLOW = Path("config/softone_workflow.example.json")


def prepared_invoice(*, errors: tuple[str, ...] = ()) -> PreparedInvoice:
    invoice = InvoiceData(
        source_path=Path("invoice.pdf"),
        supplier_name="Supplier",
        supplier_vat="123456789",
        document_number="INV-42",
        document_date=date(2026, 7, 11),
        net_value=Decimal("100.00"),
        vat_value=Decimal("24.00"),
        total_value=Decimal("124.00"),
        description="Service",
        raw_text="private",
    )
    return PreparedInvoice(
        invoice=invoice,
        settings=SupplierSettings(
            name="Supplier",
            series_code="ΤΙΜΔ",
            line_code="18103",
            payment_method="1008",
            settlement=False,
        ),
        sql_supplier=SqlSupplier(
            trdr_id=1,
            code="0227",
            name="Supplier",
            vat="123456789",
            payment="1008",
        ),
        duplicate=None,
        errors=errors,
        warnings=(),
    )


def test_workflow_profiles_are_complete() -> None:
    assert validate_workflow_profile(WORKFLOW) == []
    assert commit_is_available(WORKFLOW)


def test_context_uses_softone_mapping_and_greek_amounts() -> None:
    context = build_invoice_context(prepared_invoice())

    assert context["supplier_code"] == "0227"
    assert context["document_date"] == "11/07/2026"
    assert context["net_value"] == "100,00"


def test_preview_renders_create_workflow_without_ui_actions() -> None:
    preview = preview_workflow(WORKFLOW, "creditor_expense.create", prepared_invoice())

    assert {"id": "supplier", "action": "set", "value": "0227"} in preview
    assert preview[-2]["action"] == "save"


def test_blocked_invoice_cannot_build_automation_context() -> None:
    with pytest.raises(SoftOneAutomationError, match="BLOCKED"):
        build_invoice_context(prepared_invoice(errors=("duplicate",)))
