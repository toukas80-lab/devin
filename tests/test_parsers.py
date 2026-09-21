from datetime import date
from decimal import Decimal
from pathlib import Path

from softone_pilot.parsers.base import parse_amount, parse_date
from softone_pilot.parsers.egnatia import EgnatiaOdosParser
from softone_pilot.parsers.enartia import EnartiaParser
from softone_pilot.parsers.technomatic import TechnomaticParser


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


def test_parse_enartia_apy_receipt() -> None:
    text = """
    ENARTIA ΜΟΝΟΠΡΟΣΩΠΗ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ
    ΑΦΜ: 999082935 ΔΟΥ: ΗΡΑΚΛΕΙΟΥ
    ΤΥΠΟΣ ΠΑΡΑΣΤΑΤΙΚΟΥ ΑΡΙΘΜΟΣ ΗΜΕΡΟΜΗΝΙΑ
    Απόδειξη Παροχής Υπηρεσιών ΑΠΥ-E1L-324247 21/9/2026
    002.002 Ανανέωση Ονόματος Χώρου GR 1 53,71 0,00 0,00 53,71 24,00 12,89 66,60
    Ανανέωση του cbdcs.gr για 4 χρόνια
     ΚΑΘΑΡΗ ΑΞΙΑ 53,71
     ΑΞΙΑ Φ.Π.Α. 12,89
    ΤΕΛΙΚΗ ΑΞΙΑ 66,60
    """
    invoice = EnartiaParser().parse_text(Path("enartia.pdf"), text)
    assert invoice.document_number == "ΑΠΥ-E1L-324247"
    assert invoice.document_date == date(2026, 9, 21)
    assert invoice.net_value == Decimal("53.71")
    assert invoice.description == (
        "ΑΝΑΝΕΩΣΗ ΟΝΟΜΑΤΟΣ ΧΩΡΟΥ GR - ΑΝΑΝΕΩΣΗ ΤΟΥ CBDCS.GR ΓΙΑ 4 ΧΡΟΝΙΑ"
    )


TECHNOMATIC_TEXT = """
            TECHNOMATIC GROUP IKE
            ΑΦΜ 800745478 ΔΟΥ ΚΕΦΟΔΕ
            Αρ. Παραστατικού       Κ-ΤΙΟ             017838
   ΕΠΩΝΥΜΙΑ :           ΦΟΥΝΤΟΥΚΑΣ ΘΕΟΔΩΡΟΣ            18/09/2026
            ΚΩΔΙΚΟΣ                ΠΕΡΙΓΡΑΦΗ                  ΠΟΣΟΤΗΤΑ    ΤΙΜΗ ΜΟΝ.   %ΕΚΠΤ    ΑΞΙΑ
   130-CST220     ΜΑΓΝΗΤΙΚΟΣ ΔΙΑΚΟΠΤΗΣ CST220     Τμχ      7      25,50      25     133,87
   200-ABC               ΚΑΛΩΔΙΟ 2Μ            Τμχ      2      10,00       0      20,00
Σύνολο Ποσότητας:         9
            Άθροισμα            153,87
            ΦΠΑ            36,93
            ΣΥΝΟΛΟ            190,80  €
"""


def test_parse_technomatic_lines() -> None:
    invoice = TechnomaticParser().parse_text(Path("technomatic.pdf"), TECHNOMATIC_TEXT)
    assert invoice.document_number == "017838"
    assert invoice.document_date == date(2026, 9, 18)
    assert invoice.net_value == Decimal("153.87")
    assert invoice.vat_pct == Decimal("24")
    assert [line.code for line in invoice.lines] == ["130-CST220", "200-ABC"]
    first = invoice.lines[0]
    assert (first.quantity, first.unit_price, first.discount_pct, first.value) == (
        Decimal("7"),
        Decimal("25.50"),
        Decimal("25"),
        Decimal("133.87"),
    )
