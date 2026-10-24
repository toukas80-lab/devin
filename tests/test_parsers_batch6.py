from decimal import Decimal
from pathlib import Path

import pytest

from softone_pilot.config import load_config
from softone_pilot.devin_txt import build_txt
from softone_pilot.parsers.aegimesh import AegimeshParser
from softone_pilot.parsers.enartia import EnartiaParser
from softone_pilot.parsers.faros import GtFarosParser, TziastidisFarosParser
from softone_pilot.parsers.hellenicshipping import HellenicShippingParser
from softone_pilot.parsers.iliadis import IliadisCargoParser
from softone_pilot.parsers.jobfind import JobfindParser
from softone_pilot.parsers.registry import PARSERS
from softone_pilot.parsers.salvador import SalvadorParser
from softone_pilot.parsers.vn import VnParser

FIXTURES = Path(__file__).parent / "fixtures"
DEFAULT_CONFIG = Path(__file__).parents[1] / "src/softone_pilot/devin-config.default.json"

CASES = [
    ("enartia_2100009873", EnartiaParser, "2100009873", "2026-10-12", "7.50", "1.80", "9.30", 0),
    (
        "iliadis_06677",
        IliadisCargoParser,
        "ΗΤΠΥΓ06677",
        "2026-10-13",
        "150.00",
        "36.00",
        "186.00",
        1,
    ),
    (
        "iliadis_02693",
        IliadisCargoParser,
        "ΗΤΠΥΒ02693",
        "2026-10-23",
        "1300.00",
        "312.00",
        "1612.00",
        1,
    ),
    ("salvador_268", SalvadorParser, "000268", "2026-10-12", "4012.94", "0.00", "4012.94", 22),
    ("gtfaros_11578", GtFarosParser, "0011578", "2026-10-01", "170.00", "12.00", "182.00", 2),
    (
        "tziastidis_74869",
        TziastidisFarosParser,
        "0074869",
        "2026-10-02",
        "140.00",
        "33.60",
        "173.60",
        2,
    ),
    (
        "tziastidis_574",
        TziastidisFarosParser,
        "0000574",
        "2026-10-02",
        "328.69",
        "0.00",
        "328.69",
        1,
    ),
    ("aegimesh_44", AegimeshParser, "FT2026-44", "2026-10-06", "296.40", "0.00", "296.40", 1),
    ("aegimesh_46", AegimeshParser, "FT2026-46", "2026-10-14", "642.20", "0.00", "642.20", 1),
    ("vn_000317", VnParser, "000317", "2026-10-15", "34083.50", "0.00", "34083.50", 6),
    ("vn_000319", VnParser, "000319", "2026-10-15", "500.00", "0.00", "500.00", 1),
    ("jobfind_224867", JobfindParser, "224867", "2026-10-21", "25.00", "6.00", "31.00", 1),
]


def load(name: str) -> str:
    return (FIXTURES / f"{name}.txt").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("name", "parser", "number", "day", "net", "vat", "total", "line_count"), CASES
)
def test_batch6_invoices(name, parser, number, day, net, vat, total, line_count) -> None:
    invoice = parser().parse_text(Path(f"{name}.pdf"), load(name))
    assert invoice.document_number == number
    assert invoice.document_date.isoformat() == day
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal(net),
        Decimal(vat),
        Decimal(total),
    )
    assert len(invoice.lines) == line_count


def first_match(text: str) -> type:
    normalized = text.replace(" ", "").upper()
    return next(type(p) for p in PARSERS if p.matches(normalized))


def test_iliadis_is_not_taken_by_hellenic_shipping() -> None:
    text = load("iliadis_06677")
    assert HellenicShippingParser.vat in text
    assert first_match(text) is IliadisCargoParser


def test_vn_skewer_codes_and_three_decimal_prices() -> None:
    invoice = VnParser().parse_text(Path("vn.pdf"), load("vn_000317"))
    assert [(ln.code, ln.quantity, ln.unit_price) for ln in invoice.lines] == [
        ("240-4-SSP-BM PADDLE", Decimal("32.00"), Decimal("45.000")),
        ("215-4-SSP-BM", Decimal("120.00"), Decimal("24.705")),
        ("215-3.2-SSP-BM", Decimal("100.00"), Decimal("24.025")),
        ("240-4-SSP-BM", Decimal("928.00"), Decimal("26.800")),
        ("220-3.7-SSP-BM", Decimal("36.00"), Decimal("25.500")),
        ("240-4-SSP-BM PADD+LOG", Decimal("32.00"), Decimal("46.500")),
    ]
    assert "Scostamenti" not in " ".join(ln.description for ln in invoice.lines)


def test_batch6_rows_use_history_accounts() -> None:
    config = load_config(DEFAULT_CONFIG)
    invoices = [
        GtFarosParser().parse_text(Path("a.pdf"), load("gtfaros_11578")),
        TziastidisFarosParser().parse_text(Path("b.pdf"), load("tziastidis_74869")),
        TziastidisFarosParser().parse_text(Path("c.pdf"), load("tziastidis_574")),
        IliadisCargoParser().parse_text(Path("d.pdf"), load("iliadis_06677")),
        VnParser().parse_text(Path("e.pdf"), load("vn_000317")),
    ]
    result = build_txt(invoices, config)
    assert result.errors == ()
    accounts = [row.split(";")[4] for row in result.expense_rows]
    assert accounts == ["10033", "10034", "10034", "10001", "10009", "81004"]
    items = [row.split(";")[4] for row in result.purchase_rows]
    assert items == ["03819", "03829", "03828", "03830", "03920", "03822"]
    assert result.purchase_rows[1].split(";")[6] == "24,705"


def test_jobfind_and_vn_remote_are_mapped() -> None:
    config = load_config(DEFAULT_CONFIG)
    invoices = [
        JobfindParser().parse_text(Path("j.pdf"), load("jobfind_224867")),
        VnParser().parse_text(Path("v.pdf"), load("vn_000319")),
    ]
    result = build_txt(invoices, config)
    assert result.errors == ()
    assert result.expense_rows[0].split(";")[2:5] == ["0049", "224867", "81013"]
    assert result.purchase_rows[0].split(";")[3:6] == ["000319", "03918", "1"]
