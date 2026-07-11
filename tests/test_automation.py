import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

import softone_pilot.automation as automation
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


def test_default_window_matches_only_softone_titles() -> None:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    pattern = workflow["window"]["title_re"]

    assert re.search(pattern, "SoftOne News Page")
    assert not re.search(pattern, "Νέα λειτουργική εφαρμογή βάσης - Google Chrome")


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


def test_screenshot_failure_does_not_mask_workflow_error(monkeypatch) -> None:
    class Window:
        pass

    monkeypatch.setattr(automation, "_windows_desktop", lambda: object())
    monkeypatch.setattr(
        automation,
        "_find_window",
        lambda desktop, selector, **kwargs: Window(),
    )

    def fail_step(window, step, context):
        raise ValueError("original failure")

    def fail_screenshot(window, artifacts_dir, profile_name):
        raise OSError("disk full")

    monkeypatch.setattr(automation, "_run_step", fail_step)
    monkeypatch.setattr(automation, "_capture_failure", fail_screenshot)

    with pytest.raises(SoftOneAutomationError, match="original failure.*Screenshot: None"):
        automation.execute_workflow(
            WORKFLOW,
            "creditor_expense.create",
            prepared_invoice(),
        )


def test_missing_control_on_uia_wrapper_has_clean_error() -> None:
    class Window:
        def descendants(self):
            return []

    with pytest.raises(SoftOneAutomationError, match="Δεν βρέθηκε control"):
        automation._find_control(
            Window(),
            {"title": "missing"},
            timeout=0.01,
        )


def test_find_window_falls_back_to_launched_process() -> None:
    class ElementInfo:
        automation_id = ""
        class_name = ""
        control_type = "Window"
        name = "Login"
        process_id = 42

    class Window:
        element_info = ElementInfo()

        def rectangle(self):
            class Rectangle:
                def width(self):
                    return 100

                def height(self):
                    return 100

            return Rectangle()

    class Desktop:
        def windows(self):
            return [Window()]

    assert automation._find_window(
        Desktop(),
        {"title": "SoftOne"},
        process_id=42,
    )


def test_escape_keys_protects_send_keys_metacharacters() -> None:
    assert automation._escape_keys("a+b^c") == "a{+}b{^}c"
