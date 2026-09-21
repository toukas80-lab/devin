from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from softone_pilot.parsers.base import PdfParseError, parse_amount, parse_date
from softone_pilot.parsers.egnatia import EgnatiaOdosParser
from softone_pilot.parsers.enartia import EnartiaParser
from softone_pilot.parsers.fedex import FedexParser
from softone_pilot.parsers.karasoulis import KarasoulisParser
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
    assert {line.vat_pct for line in invoice.lines} == {Decimal("24")}


def test_technomatic_mixed_vat_is_rejected() -> None:
    text = TECHNOMATIC_TEXT.replace("36,93", "34,53").replace("190,80", "188,40")
    with pytest.raises(PdfParseError, match="ενιαίο συντελεστή"):
        TechnomaticParser().parse_text(Path("technomatic.pdf"), text)


def test_enartia_credit_note_is_rejected() -> None:
    text = """
    ENARTIA ΜΟΝΟΠΡΟΣΩΠΗ ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ ΑΦΜ 999082935
    ΠΙΣΤΩΤΙΚΟ ΠΤΠΥ-E1-734390
    Ημερομηνία Έκδοσης: 06/04/2026
    ΚΑΘΑΡΗ ΑΞΙΑ 100,00
    ΑΞΙΑ Φ.Π.Α. 24,00
    ΤΕΛΙΚΗ ΑΞΙΑ 124,00
    """
    with pytest.raises(PdfParseError, match="ΠΤΠΥ"):
        EnartiaParser().parse_text(Path("enartia.pdf"), text)


FEDEX_TEXT = """FedEx Express Greece Μονοπρόσωπη
ΑΦΜ: GR095283423
Αριθμός τιμολογίου:
685277532
08/09/2026
08/10/2026
163.98 EUR
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
ΦΠΑ Απαλ/μενη ΦΠΑ
62.7102/09/2026876620512035 0.00 62.71FedEx Intl Priority 1 6.70 kg
Υποσύνολο EURG.MICHAEL 03/09/2026 15:05Υπογραφή: 62.71
Ισχύον ΦΠΑ 24.00%
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
ΦΠΑ Απαλ/μενη ΦΠΑ
37.7831/08/2026876495715856 0.00 37.78FedEx Regional Economy 2 31.00 kg 882922841073
Ισχύον ΦΠΑ 24.00%
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
ΦΠΑ Απαλ/μενη ΦΠΑ
31.7531/08/2026876497693791 0.00 31.75FedEx Regional Economy 2 29.00 kg 882923158514
Ισχύον ΦΠΑ 24.00%
Ποσοστό\xa0ΦΠΑ Χρεώσεις ΦΠΑ Αξία
594.25 31.74 163.9824.00 %
Συνολική\xa0Αξία EUR 163.98
Έκπτωση Καθαρή\xa0Αξία
-462.01 132.24
"""


def test_parse_fedex_shipments() -> None:
    invoice = FedexParser().parse_text(Path("fedex.pdf"), FEDEX_TEXT)
    assert invoice.document_number == "685277532"
    assert invoice.document_date == date(2026, 9, 8)
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal("132.24"),
        Decimal("31.74"),
        Decimal("163.98"),
    )
    assert [line.value for line in invoice.lines] == [
        Decimal("62.71"),
        Decimal("37.78"),
        Decimal("31.75"),
    ]
    assert invoice.lines[0].code == "876620512035"
    assert invoice.lines[0].description == "FEDEX INTL PRIORITY 876620512035 02/09/2026"


def test_fedex_line_mismatch_is_rejected() -> None:
    text = FEDEX_TEXT.replace("-462.01 132.24", "-462.01 140.00")
    with pytest.raises(PdfParseError, match="Άθροισμα αποστολών"):
        FedexParser().parse_text(Path("fedex.pdf"), text)


KARASOULIS_TEXT = """ΑΦΜ/VAT.NO.:094453479 ΔΟΥ:ΦΑΕ ΘΕΣΣΑΛΟΝΙΚΗΣ
Τιμολόγιο Παροχής Υπηρεσιών 3/8/2026
ΤΠΥ-0000019455
56429
ΕΛΛΑΔΑ
VN FOOD PROCESSING EQUIPMENT SNC
COLLECORVINO
ITALY
ΦΟΥΝΤΟΥΚΑΣ ΘΕΟΔΩΡΟΣ Μ.Ι.Κ.Ε
24380,00 471,20ΝΑΥΛΟΣ / FREIGHT 91,20
24380,00 91,20
380,00
91,20
DDT 221 471,20
471,20
"""


def test_parse_karasoulis_freight() -> None:
    invoice = KarasoulisParser().parse_text(Path("karasoulis.pdf"), KARASOULIS_TEXT)
    assert invoice.document_number == "19455"
    assert invoice.document_date == date(2026, 8, 3)
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal("380.00"),
        Decimal("91.20"),
        Decimal("471.20"),
    )
    assert invoice.description == "ΝΑΥΛΟΣ VN FOOD PROCESSING EQUIPMENT SNC (ITALY)"
    assert invoice.lines[0].vat_pct == Decimal("24")


def test_karasoulis_mixed_vat_lines() -> None:
    text = KARASOULIS_TEXT.replace(
        "24380,00 471,20ΝΑΥΛΟΣ / FREIGHT 91,20",
        "24380,00 471,20ΝΑΥΛΟΣ / FREIGHT 91,20\n020,00 20,00ΕΞΟΔΑ / FEES 0,00",
    ).replace("\n471,20\n", "\n491,20\n")
    invoice = KarasoulisParser().parse_text(Path("karasoulis.pdf"), text)
    assert [(line.value, line.vat_pct) for line in invoice.lines] == [
        (Decimal("380.00"), Decimal("24")),
        (Decimal("20.00"), Decimal("0")),
    ]
    assert invoice.total_value == Decimal("491.20")
