from dataclasses import fields, replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from softone_pilot.config import AppConfig, default_config
from softone_pilot.devin_txt import EXPENSE_FILE, PURCHASE_FILE, build_txt, fmt, write_txt
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
                Decimal("24"),
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
                trdr_code="0237",
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
    assert result.purchase_rows == ("18/09/2026;ΤΔΑ;0237;017838;03762;7;25,5;24;25",)


def test_unmapped_item_blocks_document() -> None:
    result = build_txt([purchase_invoice()], config({}))
    assert result.purchase_rows == ()
    assert "130-CST220" in result.errors[0]


def test_duplicate_in_batch_is_reported() -> None:
    result = build_txt([expense_invoice(), expense_invoice()], config({}))
    assert len(result.expense_rows) == 1
    assert "διπλό" in result.errors[0]


def test_purchase_rows_use_line_vat() -> None:
    base = purchase_invoice()
    invoice = InvoiceData(
        **{
            **{f.name: getattr(base, f.name) for f in fields(base)},
            "net_value": Decimal("153.87"),
            "vat_value": Decimal("34.53"),
            "total_value": Decimal("188.40"),
            "lines": (
                *base.lines,
                InvoiceLine(
                    "200-ABC",
                    "ΒΙΒΛΙΟ",
                    Decimal("2"),
                    Decimal("10"),
                    Decimal("0"),
                    Decimal("20"),
                    Decimal("6"),
                ),
            ),
        }
    )
    result = build_txt([invoice], config({"130-CST220": "03762", "200-ABC": "00010"}))
    assert result.errors == ()
    assert [row.split(";")[7] for row in result.purchase_rows] == ["24", "6"]


def test_expense_lines_produce_one_row_each() -> None:
    base = expense_invoice()
    invoice = InvoiceData(
        **{
            **{f.name: getattr(base, f.name) for f in fields(base)},
            "net_value": Decimal("100.00"),
            "vat_value": Decimal("24.00"),
            "total_value": Decimal("124.00"),
            "lines": (
                InvoiceLine(
                    "A",
                    "ΑΠΟΣΤΟΛΗ Α",
                    Decimal("1"),
                    Decimal("60"),
                    Decimal("0"),
                    Decimal("60"),
                    Decimal("24"),
                ),
                InvoiceLine(
                    "B",
                    "ΑΠΟΣΤΟΛΗ Β",
                    Decimal("1"),
                    Decimal("40"),
                    Decimal("0"),
                    Decimal("40"),
                    Decimal("24"),
                ),
            ),
        }
    )
    result = build_txt([invoice], config({}))
    assert result.expense_rows == (
        "21/09/2026;ΤΙΜΔ;0077;E1L-324247;81013;60;24;ΑΠΟΣΤΟΛΗ Α (ΑΠΥ-E1L-324247)",
        "21/09/2026;ΤΙΜΔ;0077;E1L-324247;81013;40;24;ΑΠΟΣΤΟΛΗ Β (ΑΠΥ-E1L-324247)",
    )


def test_write_txt_removes_stale_files(tmp_path: Path) -> None:
    both = build_txt([expense_invoice(), purchase_invoice()], config({"130-CST220": "03762"}))
    write_txt(both, tmp_path)
    assert (tmp_path / EXPENSE_FILE).exists() and (tmp_path / PURCHASE_FILE).exists()

    only_expense = build_txt([expense_invoice()], config({}))
    written = write_txt(only_expense, tmp_path)
    assert written == [tmp_path / EXPENSE_FILE]
    assert not (tmp_path / PURCHASE_FILE).exists()


def test_purchase_is_complete_requires_item_map_not_line_code() -> None:
    purchase = config({"130-CST220": "03762"}).suppliers["800745478"]
    assert purchase.is_complete
    assert not config({}).suppliers["800745478"].is_complete
    expense = config({}).suppliers["999082935"]
    assert expense.is_complete
    assert not replace(expense, line_code="").is_complete


def test_expense_line_category_selects_account() -> None:
    base = expense_invoice()
    invoice = InvoiceData(
        **{
            **{f.name: getattr(base, f.name) for f in fields(base)},
            "lines": (
                InvoiceLine(
                    "A",
                    "ΕΞΑΓΩΓΗ",
                    Decimal("1"),
                    Decimal("60"),
                    Decimal("0"),
                    Decimal("60"),
                    Decimal("24"),
                    "export24",
                ),
                InvoiceLine(
                    "B",
                    "ΕΙΣΑΓΩΓΗ",
                    Decimal("1"),
                    Decimal("40"),
                    Decimal("0"),
                    Decimal("40"),
                    Decimal("24"),
                    "import24",
                ),
            ),
        }
    )
    fedex = replace(
        config({}).suppliers["999082935"],
        line_code="",
        line_codes={"export24": "10016", "import24": "10002"},
    )
    cfg = AppConfig(sql=default_config().sql, suppliers={"999082935": fedex})
    assert fedex.is_complete
    result = build_txt([invoice], cfg)
    assert [row.split(";")[4] for row in result.expense_rows] == ["10016", "10002"]

    missing = AppConfig(
        sql=default_config().sql,
        suppliers={"999082935": replace(fedex, line_codes={"export24": "10016"})},
    )
    result = build_txt([invoice], missing)
    assert result.expense_rows == ()
    assert "import24" in result.errors[0]
