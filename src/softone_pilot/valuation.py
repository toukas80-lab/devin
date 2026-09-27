from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
CENT = Decimal("0.01")


def money(value: Decimal | float | int | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class YearFigures:
    fiscal_year: int
    revenue: Decimal
    cost_of_goods: Decimal
    operating_expenses: Decimal | None

    @property
    def gross_profit(self) -> Decimal:
        return money(self.revenue - self.cost_of_goods)

    @property
    def gross_margin(self) -> Decimal | None:
        if self.revenue == ZERO:
            return None
        return (self.gross_profit / self.revenue).quantize(Decimal("0.0001"))

    def ebitda(self, opex_ratio: Decimal | None) -> Decimal:
        if self.operating_expenses is not None:
            return money(self.gross_profit - self.operating_expenses)
        if opex_ratio is not None:
            return money(self.gross_profit - self.revenue * opex_ratio)
        return self.gross_profit

    def to_dict(self, opex_ratio: Decimal | None) -> dict:
        return {
            "fiscal_year": self.fiscal_year,
            "revenue": str(money(self.revenue)),
            "cost_of_goods": str(money(self.cost_of_goods)),
            "gross_profit": str(self.gross_profit),
            "gross_margin": str(self.gross_margin) if self.gross_margin is not None else None,
            "operating_expenses": (
                str(money(self.operating_expenses)) if self.operating_expenses is not None else None
            ),
            "ebitda": str(self.ebitda(opex_ratio)),
        }


@dataclass(frozen=True)
class BalanceSnapshot:
    inventory_value: Decimal
    receivables: Decimal
    payables: Decimal
    cash: Decimal

    @property
    def net_assets(self) -> Decimal:
        return money(self.inventory_value + self.receivables + self.cash - self.payables)

    def to_dict(self) -> dict:
        data = {key: str(money(value)) for key, value in asdict(self).items()}
        data["net_assets"] = str(self.net_assets)
        return data


@dataclass(frozen=True)
class ValuationAssumptions:
    multiple_low: Decimal = Decimal("3")
    multiple_mid: Decimal = Decimal("4")
    multiple_high: Decimal = Decimal("5")
    discount_rate: Decimal = Decimal("0.12")
    terminal_growth: Decimal = Decimal("0.01")
    longevity_premium: Decimal = Decimal("0.10")
    opex_ratio: Decimal | None = None
    projection_years: int = 5


@dataclass(frozen=True)
class ValuationResult:
    years: tuple[YearFigures, ...]
    balance: BalanceSnapshot
    assumptions: ValuationAssumptions
    normalized_ebitda: Decimal
    revenue_cagr: Decimal | None
    asset_based: Decimal
    earnings_low: Decimal
    earnings_mid: Decimal
    earnings_high: Decimal
    dcf: Decimal
    indicative_low: Decimal
    indicative_mid: Decimal
    indicative_high: Decimal
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        assumptions = {
            key: (str(value) if value is not None else None)
            for key, value in asdict(self.assumptions).items()
        }
        return {
            "years": [year.to_dict(self.assumptions.opex_ratio) for year in self.years],
            "balance": self.balance.to_dict(),
            "assumptions": assumptions,
            "normalized_ebitda": str(self.normalized_ebitda),
            "revenue_cagr": str(self.revenue_cagr) if self.revenue_cagr is not None else None,
            "methods": {
                "asset_based": str(self.asset_based),
                "earnings_multiple": {
                    "low": str(self.earnings_low),
                    "mid": str(self.earnings_mid),
                    "high": str(self.earnings_high),
                },
                "dcf": str(self.dcf),
            },
            "indicative_value": {
                "low": str(self.indicative_low),
                "mid": str(self.indicative_mid),
                "high": str(self.indicative_high),
            },
            "warnings": list(self.warnings),
        }


def normalized_ebitda(years: list[YearFigures], opex_ratio: Decimal | None) -> Decimal:
    ordered = sorted(years, key=lambda year: year.fiscal_year)
    total = sum(year.ebitda(opex_ratio) * (i + 1) for i, year in enumerate(ordered))
    return money(total / sum(range(1, len(ordered) + 1)))


def revenue_cagr(years: list[YearFigures]) -> Decimal | None:
    ordered = sorted(years, key=lambda year: year.fiscal_year)
    if len(ordered) < 2 or ordered[0].revenue <= ZERO or ordered[-1].revenue <= ZERO:
        return None
    periods = ordered[-1].fiscal_year - ordered[0].fiscal_year
    if periods <= 0:
        return None
    ratio = float(ordered[-1].revenue / ordered[0].revenue)
    return Decimal(str(round(ratio ** (1 / periods) - 1, 4)))


def discounted_cash_flow(
    ebitda: Decimal,
    growth: Decimal | None,
    assumptions: ValuationAssumptions,
) -> Decimal:
    if ebitda <= ZERO:
        return ZERO
    growth_rate = min(growth if growth is not None else ZERO, Decimal("0.05"))
    rate = assumptions.discount_rate
    if rate <= assumptions.terminal_growth:
        raise ValueError("discount_rate πρέπει να είναι μεγαλύτερο από terminal_growth")
    value = ZERO
    cash_flow = ebitda
    for year in range(1, assumptions.projection_years + 1):
        cash_flow = cash_flow * (1 + growth_rate)
        value += cash_flow / (1 + rate) ** year
    terminal = cash_flow * (1 + assumptions.terminal_growth) / (rate - assumptions.terminal_growth)
    value += terminal / (1 + rate) ** assumptions.projection_years
    return money(value)


def compute_valuation(
    years: list[YearFigures],
    balance: BalanceSnapshot,
    assumptions: ValuationAssumptions | None = None,
) -> ValuationResult:
    assumptions = assumptions or ValuationAssumptions()
    if not years:
        raise ValueError("Δεν υπάρχουν οικονομικές χρήσεις για αποτίμηση")

    warnings: list[str] = []
    if assumptions.opex_ratio is None and any(y.operating_expenses is None for y in years):
        warnings.append(
            "Δεν βρέθηκαν λειτουργικά έξοδα (Γενική Λογιστική): το EBITDA ισούται με το "
            "μικτό κέρδος και ΥΠΕΡΕΚΤΙΜΑ την αξία. Δώσε --opex-ratio."
        )
    if len(years) < 3:
        warnings.append("Λιγότερες από 3 χρήσεις: το CAGR και η κανονικοποίηση είναι αδύναμα.")

    ebitda = normalized_ebitda(years, assumptions.opex_ratio)
    cagr = revenue_cagr(years)
    premium = 1 + assumptions.longevity_premium
    net_cash = money(balance.cash - balance.payables)

    earnings = [
        money(ebitda * multiple * premium + net_cash)
        for multiple in (
            assumptions.multiple_low,
            assumptions.multiple_mid,
            assumptions.multiple_high,
        )
    ]
    dcf = money(discounted_cash_flow(ebitda, cagr, assumptions) + net_cash)
    asset_based = balance.net_assets

    candidates = [asset_based, earnings[1], dcf]
    return ValuationResult(
        years=tuple(sorted(years, key=lambda year: year.fiscal_year)),
        balance=balance,
        assumptions=assumptions,
        normalized_ebitda=ebitda,
        revenue_cagr=cagr,
        asset_based=asset_based,
        earnings_low=earnings[0],
        earnings_mid=earnings[1],
        earnings_high=earnings[2],
        dcf=dcf,
        indicative_low=min(min(candidates), earnings[0]),
        indicative_mid=money(sum(candidates) / len(candidates)),
        indicative_high=max(max(candidates), earnings[2]),
        warnings=tuple(warnings),
    )


def format_report(result: ValuationResult) -> str:
    lines = ["ΑΠΟΤΙΜΗΣΗ ΕΤΑΙΡΙΑΣ (read-only SoftOne)", ""]
    lines.append(f"{'Χρήση':>6} {'Πωλήσεις':>14} {'Κόστος':>14} {'Μικτό':>14} {'EBITDA':>14}")
    for year in result.years:
        lines.append(
            f"{year.fiscal_year:>6} {money(year.revenue):>14,.2f} "
            f"{money(year.cost_of_goods):>14,.2f} {year.gross_profit:>14,.2f} "
            f"{year.ebitda(result.assumptions.opex_ratio):>14,.2f}"
        )
    lines.append("")
    cagr = f"{result.revenue_cagr * 100:.1f}%" if result.revenue_cagr is not None else "n/a"
    lines.append(f"Κανονικοποιημένο EBITDA (σταθμισμένο): {result.normalized_ebitda:,.2f}")
    lines.append(f"CAGR πωλήσεων: {cagr}")
    balance = result.balance
    lines.append("")
    lines.append(f"Απόθεμα (κόστος):       {balance.inventory_value:>14,.2f}")
    lines.append(f"Απαιτήσεις πελατών:     {balance.receivables:>14,.2f}")
    lines.append(f"Ταμείο/τράπεζες:        {balance.cash:>14,.2f}")
    lines.append(f"Υποχρεώσεις προμηθευτών:{balance.payables:>14,.2f}")
    lines.append(f"Καθαρή θέση (assets):   {balance.net_assets:>14,.2f}")
    lines.append("")
    a = result.assumptions
    lines.append(
        f"Πολλαπλασιαστής EBITDA x{a.multiple_low}/{a.multiple_mid}/{a.multiple_high} "
        f"(+{a.longevity_premium * 100:.0f}% premium μακροβιότητας):"
    )
    lines.append(
        f"  {result.earnings_low:,.2f} / {result.earnings_mid:,.2f} / {result.earnings_high:,.2f}"
    )
    lines.append(
        f"DCF ({a.projection_years} έτη, WACC {a.discount_rate * 100:.0f}%): {result.dcf:,.2f}"
    )
    lines.append("")
    lines.append(
        f"ΕΝΔΕΙΚΤΙΚΗ ΑΞΙΑ: {result.indicative_low:,.2f} - {result.indicative_high:,.2f} "
        f"(μέση {result.indicative_mid:,.2f})"
    )
    for warning in result.warnings:
        lines.append(f"WARNING: {warning}")
    return "\n".join(lines)
