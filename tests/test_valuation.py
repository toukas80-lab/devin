from decimal import Decimal

from softone_pilot.valuation import (
    BalanceSnapshot,
    ValuationAssumptions,
    YearFigures,
    compute_valuation,
    format_report,
    revenue_cagr,
)


def _years(with_expenses: bool = True) -> list[YearFigures]:
    return [
        YearFigures(
            fiscal_year=2020 + i,
            revenue=Decimal(1_000_000 + 50_000 * i),
            cost_of_goods=Decimal(600_000 + 30_000 * i),
            operating_expenses=Decimal(250_000) if with_expenses else None,
        )
        for i in range(6)
    ]


BALANCE = BalanceSnapshot(
    inventory_value=Decimal("120000"),
    receivables=Decimal("80000"),
    payables=Decimal("90000"),
    cash=Decimal("40000"),
)


def test_cagr_uses_first_and_last_year() -> None:
    assert revenue_cagr(_years()) == Decimal("0.0456")


def test_valuation_with_general_ledger_expenses() -> None:
    result = compute_valuation(_years(), BALANCE)
    assert result.asset_based == Decimal("150000.00")
    assert result.normalized_ebitda == Decimal("216666.67")
    assert result.earnings_mid == Decimal("903333.35")
    assert result.earnings_low < result.earnings_mid < result.earnings_high
    assert result.indicative_low <= result.indicative_mid <= result.indicative_high
    assert result.warnings == ()


def test_missing_expenses_warns_and_opex_ratio_fixes_it() -> None:
    warned = compute_valuation(_years(with_expenses=False), BALANCE)
    assert any("ΥΠΕΡΕΚΤΙΜΑ" in warning for warning in warned.warnings)

    fixed = compute_valuation(
        _years(with_expenses=False),
        BALANCE,
        ValuationAssumptions(opex_ratio=Decimal("0.25")),
    )
    assert fixed.warnings == ()
    assert fixed.normalized_ebitda < warned.normalized_ebitda


def test_report_and_json_render() -> None:
    result = compute_valuation(_years(), BALANCE)
    text = format_report(result)
    assert "ΕΝΔΕΙΚΤΙΚΗ ΑΞΙΑ" in text
    payload = result.to_dict()
    assert len(payload["years"]) == 6
    assert payload["methods"]["asset_based"] == "150000.00"
