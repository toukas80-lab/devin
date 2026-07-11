from datetime import date
from decimal import Decimal
from pathlib import Path

from softone_pilot.parsers.base import parse_amount, parse_date
from softone_pilot.parsers.egnatia import EgnatiaOdosParser
from softone_pilot.parsers.enartia import EnartiaParser


def test_parse_greek_amounts() -> None:
    assert parse_amount("1.234,56 €") == Decimal("1234.56")
    assert parse_amount("74,50") == Decimal("74.50")


def test_parse_greek_date() -> None:
    assert parse_date("06/04/2026") == date(2026, 4, 6)


def test_parse_enartia_text() -> None:
    text = """
    ENARTIA ΜΟΝΟΠΡΟΣΩΠΗ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ ΑΦΜ 999082935
    ΤΠΥ-E1-734386
    Ημερομηνία Έκδοσης: 06/04/2026
    Αγορά Πακέτου Φιλοξενίας Web Hosting - Standard linux
    ΚΑΘΑΡΗ ΑΞΙΑ 100,00
    ΑΞΙΑ Φ.Π.Α. 24,00
    ΤΕΛΙΚΗ ΑΞΙΑ 124,00
    """
    invoice = EnartiaParser().parse_text(Path("enartia.pdf"), text)
    assert invoice.document_number == "ΤΠΥ-E1-734386"
    assert invoice.document_date == date(2026, 4, 6)
    assert invoice.total_value == Decimal("124.00")


def test_parse_egnatia_text_and_previous_month_description() -> None:
    text = """
    ΕΓΝΑΤΙΑ ΟΔΟΣ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ ΑΦΜ: EL802408691
    INV 9328198
    01/04/2026 10:30
    ΣΥΝΟΛΑ 16,33 3,92
    ΓΕΝΙΚΟ ΣΥΝΟΛΟ: EUR 20,25
    """
    invoice = EgnatiaOdosParser().parse_text(Path("egnatia.pdf"), text)
    assert invoice.document_number == "INV-9328198"
    assert invoice.document_date == date(2026, 4, 1)
    assert invoice.description == "ΔΙΟΔΙΑ ΜΑΡΤΙΟΥ 2026"
