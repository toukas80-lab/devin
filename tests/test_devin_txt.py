from datetime import date
from decimal import Decimal
from pathlib import Path

from softone_pilot.config import AppConfig, default_config
from softone_pilot.devin_txt import build_txt, fmt
from softone_pilot.models import InvoiceData, InvoiceLine, SupplierSettings


def expense_invoice() -> InvoiceData:
    return InvoiceData(
        source_path=Path("enartia.pdf"),
        supplier_name="ENARTIA",
        supplier_vat="999082935",
        document_number="ΑΠΥ-E1L-324247",
        document_date=date(2026, 9, 21),
        net_value=Decimal("53.71"),
        vat_value=Decimal("12.89"),
        total_value=Decimal("66.60"),
        description="ΑΝΑΝΕΩΣΗ cbdcs.gr",
        raw_text="",
    )


def purchase_invoice() -> InvoiceData:
    return InvoiceData(
        source_path=Path("technomatic.pdf"),
        supplier_name="TECHNOMATIC",
        supplier_vat="800745478",
        document_number="017838",
        document_date=date(2026, 9, 18),
        net_value=Decimal("133.87"),
        vat_value=Decimal("32.13"),
        total_value=Decimal("166.00"),
        description="Κ-ΤΙΟ 017838",
        raw_text="",
        lines=(
            InvoiceLine(
                "130-CST220",
                "ΔΙΑΚΟΠΤΗΣ",
                Decimal("7"),
                Decimal("25.50"),
                Decimal("25"),
                Decimal("133.87"),
            ),
        ),
    )


def config(item_map: dict[str, str]) -> AppConfig:
    return AppConfig(
        sql=default_config().sql,
        suppliers={
            "999082935": SupplierSettings(
                name="ENARTIA",
                series_code="ΤΙΜΔ",
                line_code="81013",
                payment_method="1000",
                settlement=False,
                kind="expense",
                trdr_code="0077",
            ),
            "800745478": SupplierSettings(
                name="TECHNOMATIC",
                series_code="ΤΔΑ",
                line_code="",
                payment_method="1008",
                settlement=False,
                kind="purchase",
                trdr_code="0273",
                item_map=item_map,
            ),
        },
    )


def test_fmt_uses_comma_and_trims_zeros() -> None:
    assert fmt(Decimal("53.71")) == "53,71"
    assert fmt(Decimal("25.50")) == "25,5"
    assert fmt(Decimal("7.00")) == "7"
    assert fmt(Decimal("100.00")) == "100"


def test_expense_and_purchase_rows() -> None:
    result = build_txt([expense_invoice(), purchase_invoice()], config({"130-CST220": "03762"}))
    assert result.errors == ()
    assert result.expense_rows == (
        "21/09/2026;ΤΙΜΔ;0077;E1L-324247;81013;53,71;24;ΑΝΑΝΕΩΣΗ cbdcs.gr (ΑΠΥ-E1L-324247)",
    )
    assert result.purchase_rows == ("18/09/2026;ΤΔΑ;0273;017838;03762;7;25,5;24;25",)


def test_unmapped_item_blocks_document() -> None:
    result = build_txt([purchase_invoice()], config({}))
    assert result.purchase_rows == ()
    assert "130-CST220" in result.errors[0]


def test_duplicate_in_batch_is_reported() -> None:
    result = build_txt([expense_invoice(), expense_invoice()], config({}))
    assert len(result.expense_rows) == 1
    assert "διπλό" in result.errors[0]
