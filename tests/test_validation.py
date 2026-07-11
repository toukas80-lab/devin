from datetime import date
from decimal import Decimal
from pathlib import Path

from softone_pilot.models import InvoiceData, SupplierSettings
from softone_pilot.validation import validate_invoice


def invoice() -> InvoiceData:
    return InvoiceData(
        source_path=Path("invoice.pdf"),
        supplier_name="Supplier",
        supplier_vat="123456789",
        document_number="INV-1",
        document_date=date(2026, 7, 1),
        net_value=Decimal("100.00"),
        vat_value=Decimal("24.00"),
        total_value=Decimal("124.00"),
        description="Service",
        raw_text="",
    )


def test_complete_settings_are_ready() -> None:
    settings = SupplierSettings(
        name="Supplier",
        series_code="SERIES",
        line_code="LINE",
        payment_method="1008",
        settlement=False,
    )
    errors, warnings = validate_invoice(invoice(), settings)
    assert errors == []
    assert warnings == []


def test_missing_settings_block_automation() -> None:
    errors, warnings = validate_invoice(invoice(), None)
    assert errors
    assert warnings == []
