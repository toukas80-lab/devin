from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from softone_pilot import fx
from softone_pilot.config import default_config
from softone_pilot.devin_txt import build_txt
from softone_pilot.fx import FxError, convert_to_eur, eur_per_usd, parse_ecb_usd_rates, parse_rate
from softone_pilot.models import InvoiceData, InvoiceLine, SupplierSettings

ECB_XML = """<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
 xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
<Cube>
<Cube time="2026-05-07"><Cube currency="USD" rate="1.1628"/><Cube currency="JPY" rate="160"/></Cube>
<Cube time="2026-05-08"><Cube currency="USD" rate="1.1650"/></Cube>
</Cube>
</gesmes:Envelope>
"""


def usd_invoice() -> InvoiceData:
    line = InvoiceLine(
        "",
        "OVERAGE CREDITS",
        Decimal("1"),
        Decimal("20"),
        Decimal("0"),
        Decimal("20"),
        Decimal("0"),
    )
    return InvoiceData(
        source_path=Path("c.pdf"),
        supplier_name="COGNITION AI INC - DEVIN",
        supplier_vat="COGNITION",
        document_number="ZZCYINBS-107",
        document_date=date(2026, 5, 9),
        net_value=Decimal("20.00"),
        vat_value=Decimal("0.00"),
        total_value=Decimal("20.00"),
        description="DEVIN OVERAGE CREDITS",
        raw_text="",
        vat_pct=Decimal("0"),
        lines=(line,),
        currency="USD",
    )


def test_ecb_resolver_falls_back_to_full_history(monkeypatch: pytest.MonkeyPatch) -> None:
    feeds = {
        fx.ECB_90D_URL: {date(2026, 9, 21): Decimal("1.1490")},
        fx.ECB_HIST_URL: {
            date(2026, 5, 15): Decimal("1.1200"),
            date(2026, 9, 21): Decimal("1.1490"),
        },
    }
    calls: list[str] = []

    def fake_fetch(url: str) -> dict[date, Decimal]:
        calls.append(url)
        return feeds[url]

    monkeypatch.setattr(fx, "fetch_ecb_usd_rates", fake_fetch)
    resolver = fx.rate_resolver(None)
    assert resolver(date(2026, 9, 21)) == Decimal("0.8703")
    assert calls == [fx.ECB_90D_URL]
    assert resolver(date(2026, 5, 17)) == Decimal("0.8929")
    assert calls == [fx.ECB_90D_URL, fx.ECB_HIST_URL]
    with pytest.raises(FxError):
        resolver(date(2026, 1, 5))
    assert len(calls) == 2


def test_ecb_rate_uses_last_published_day_on_or_before() -> None:
    rates = parse_ecb_usd_rates(ECB_XML)
    assert eur_per_usd(rates, date(2026, 5, 7)) == Decimal("0.8600")
    assert eur_per_usd(rates, date(2026, 5, 9)) == Decimal("0.8584")  # Saturday -> Friday 8/5
    with pytest.raises(FxError):
        eur_per_usd(rates, date(2026, 5, 6))
    with pytest.raises(FxError):
        eur_per_usd(rates, date(2026, 5, 20))


def test_convert_usd_invoice_to_eur_keeps_audit_trail() -> None:
    eur = convert_to_eur(usd_invoice(), parse_rate("0,8585"))
    assert eur.currency == "EUR"
    assert (eur.net_value, eur.vat_value, eur.total_value) == (
        Decimal("17.17"),
        Decimal("0.00"),
        Decimal("17.17"),
    )
    assert eur.lines[0].value == Decimal("17.17")
    assert eur.lines[0].description == "OVERAGE CREDITS $20,00 X 0,8585"


def test_convert_rejects_usd_with_tax_and_bad_rate() -> None:
    with pytest.raises(FxError):
        convert_to_eur(replace(usd_invoice(), vat_value=Decimal("1.00")), Decimal("0.9"))
    with pytest.raises(FxError):
        parse_rate("abc")


def test_vat_ids_map_zero_percent_to_softone_id() -> None:
    config = replace(
        default_config(),
        suppliers={
            "COGNITION": SupplierSettings(
                name="COGNITION",
                series_code="ΤΔΕΕ",
                line_code="81013",
                payment_method="1006",
                settlement=False,
                trdr_code="0238",
            )
        },
        vat_ids={"0": "1430"},
    )
    eur = convert_to_eur(usd_invoice(), Decimal("0.8585"))
    result = build_txt([eur], config)
    assert result.errors == ()
    assert result.expense_rows == (
        "09/05/2026;ΤΔΕΕ;0238;ZZCYINBS-107;81013;17,17;ID:1430;"
        "OVERAGE CREDITS $20,00 X 0,8585 (ZZCYINBS-107)",
    )
