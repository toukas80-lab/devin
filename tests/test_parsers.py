from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from softone_pilot.parsers.base import PdfParseError, parse_amount, parse_date
from softone_pilot.parsers.cognition import CognitionParser
from softone_pilot.parsers.egnatia import EgnatiaOdosParser
from softone_pilot.parsers.enartia import EnartiaParser
from softone_pilot.parsers.fedex import FedexParser
from softone_pilot.parsers.finloup import FinloupLeasing1Parser, FinloupLeasing2Parser
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
268.07Αποστολέας Παραλήπτης Χρέωση Μεταφορικών
-225.63FOUNTOUKAS THEODOROS STOCKHOLM COUNTY, SWEDEN Εκπτωση
Υποσύνολο EURG.MICHAEL 03/09/2026 15:05Υπογραφή: 62.71
Ισχύον ΦΠΑ 24.00%
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
ΦΠΑ Απαλ/μενη ΦΠΑ
37.7831/08/2026876495715856 0.00 37.78FedEx Regional Economy 2 31.00 kg 882922841073
154.17Αποστολέας Παραλήπτης Χρέωση Μεταφορικών
-125.11SABAN ERYASAR ORAIOKASTRO, GREECE Εκπτωση
Ισχύον ΦΠΑ 24.00%
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
ΦΠΑ Απαλ/μενη ΦΠΑ
31.7531/08/2026876497693791 0.00 31.75FedEx Regional Economy 2 29.00 kg 882923158514
135.69Αποστολέας Παραλήπτης Χρέωση Μεταφορικών
-111.27EMI PATRIZIO ORAIOKASTRO, GREECE Εκπτωση
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
    assert [line.category for line in invoice.lines] == ["export24", "import24", "import24"]


FEDEX_EXEMPT_TEXT = """FedEx Express Greece Μονοπρόσωπη
ΑΦΜ: GR095283423
685269238
25/08/2026
24/09/2026
55.09 EUR
Απόδειξη Ναύλων ­ Λεπτομερείς
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
12.0305/08/2026875343928958 0.00 12.03Economy Service 1 3.20 kg 882868182063
54.66Αποστολέας Παραλήπτης Χρέωση Μεταφορικών
-46.39FOUNTOUKAS THEODOROS MEGAM EMPORIKI LTD Εκπτωση
Υποσύνολο EURA.NDREAS GEORGIOU 18/08/2026 12:31Υπογραφή: 12.03
Ισχύον ΦΠΑ 24.00%
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
0.0006/08/2026875403298141 40.17 40.17Economy Service 1 8.94 kg
2.40Αποστολέας Παραλήπτης Χρέωση διαχείρισης εκτελωνισμού εισαγωγών
186.20FOUNTOUKAS THEODOROS JORDAN LAUDANO Χρέωση Μεταφορικών
Υποσύνολο EURM.Metchin 20/08/2026 10:45Υπογραφή: 40.17
Ποσοστό ΦΠΑ Χρεώσεις ΦΠΑ Αξία
58.42 2.89 14.9224.00 %
0,00% 200.41 0.00 40.17
Συνολική Αξία EUR 55.09
Έκπτωση Καθαρή Αξία
-46.39 12.03
-160.24 40.17
Κάθε αποστολή
"""

FEDEX_DUTY_TEXT = """FedEx Express Greece Μονοπρόσωπη
ΑΦΜ: GR095283423
685275826
03/09/2026
Πληρωμή με απόδειξη
53.04 EUR
Απόδειξη Δασμών & Φόρων ­ Λεπτομερείς
ΥπηρεσίαΑρ. Αποστολής Ημερομηνία
10/06/2026872826082908 39.23 53.04Economy Service 13.81 0.00 0.00
13.3715.00Αποστολέας Παραλήπτης Χρέωση δαπανών
13.8115.49FOUNTOUKAS THEODOROS WASHINGTON, UNITED STATES Επαναχρέωση Δασμών
Υποσύνολο EUR25/06/2026Υπογραφή: 53.04
Άλλες χρεώσεις με τιμή 0,00% 25.86
ΦΠΑ σε 0.00 % 0.00
EUR 53.04Συνολική Αξία
"""


def test_parse_fedex_export_with_exempt_shipment() -> None:
    invoice = FedexParser().parse_text(Path("fedex.pdf"), FEDEX_EXEMPT_TEXT)
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal("52.20"),
        Decimal("2.89"),
        Decimal("55.09"),
    )
    assert [(line.value, line.vat_pct, line.category) for line in invoice.lines] == [
        (Decimal("12.03"), Decimal("24"), "export24"),
        (Decimal("40.17"), Decimal("0"), "export0"),
    ]
    assert invoice.lines[1].description == "ECONOMY SERVICE 875403298141 06/08/2026"


def test_parse_fedex_duty_receipt() -> None:
    invoice = FedexParser().parse_text(Path("fedex.pdf"), FEDEX_DUTY_TEXT)
    assert invoice.document_number == "685275826"
    assert invoice.document_date == date(2026, 9, 3)
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal("53.04"),
        Decimal("0"),
        Decimal("53.04"),
    )
    assert [(line.value, line.vat_pct, line.category) for line in invoice.lines] == [
        (Decimal("53.04"), Decimal("0"), "duty")
    ]
    assert invoice.description == "ΔΑΣΜΟΙ FEDEX 1 ΑΠΟΣΤΟΛΕΣ"


def test_fedex_duty_receipt_with_vat_is_rejected() -> None:
    text = FEDEX_DUTY_TEXT.replace("ΦΠΑ σε 0.00 % 0.00", "ΦΠΑ σε 24.00 % 3.21")
    with pytest.raises(PdfParseError, match="δασμών FEDEX με ΦΠΑ"):
        FedexParser().parse_text(Path("fedex.pdf"), text)


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


COGNITION_TEXT = """\xa0
Invoice
Invoice number ZZCYINBS\x000107
Date of issue September 21, 2026
Cognition AI Inc.
Bill to
FOUNTOUKAS THEODOROS MON.IKE
GR VAT EL802313849
$20.00 USD due September 21, 2026
Description Qty Unit price Tax Amount
Overage credits 1 $20.00 0% $20.00
Subtotal $20.00
Total $20.00
Amount due $20.00\xa0USD
\x001\x00 Tax to be paid on reverse charge basis
"""


def test_parse_cognition_usd_reverse_charge() -> None:
    parser = CognitionParser()
    assert parser.matches(COGNITION_TEXT.replace(" ", "").upper())
    invoice = parser.parse_text(Path("cognition.pdf"), COGNITION_TEXT)
    assert invoice.currency == "USD"
    assert invoice.document_number == "ZZCYINBS-107"
    assert invoice.document_date == date(2026, 9, 21)
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal("20.00"),
        Decimal("0.00"),
        Decimal("20.00"),
    )
    assert invoice.lines[0].vat_pct == 0


def test_parse_cognition_subscription_line_with_period() -> None:
    text = COGNITION_TEXT.replace(
        "Overage credits 1 $20.00 0% $20.00",
        "Pro\nMay 30 Jun 30, 2026\n1 $20.00 0% $20.00",
    )
    invoice = CognitionParser().parse_text(Path("cognition.pdf"), text)
    assert [line.description for line in invoice.lines] == ["PRO (MAY 30 JUN 30, 2026)"]
    assert invoice.description == "DEVIN PRO (MAY 30 JUN 30, 2026)"
    assert invoice.net_value == Decimal("20.00")


def test_cognition_rejects_taxed_invoice() -> None:
    text = COGNITION_TEXT.replace("Total $20.00", "Total $24.80").replace(
        "Amount due $20.00", "Amount due $24.80"
    )
    with pytest.raises(PdfParseError, match="φόρο"):
        CognitionParser().parse_text(Path("cognition.pdf"), text)


FINLOUP_EINVOICE_TEXT = """FINLOUP LEASING II ΜΟΝΟΠΡΟΣΩΠΗ  Α  Ε  Αρ . Εγκατάστασης  Εδρα
ΓΡΑΦΕΙΟΥ  ΚΑΙ  ΑΦΜ  EL803183981 Δ. Ο . Υ . ΚΕΦΟΔΕ  ΑΤΤΙΚΗΣ  Αριθμός  ΓΕΜΗ
Είδος  Παραστατικού
Τιμολόγιο  Παροχής  Υπηρεσιών
Αριθμός
ΤΠΥ 0000988
Ημερομηνία  Έκδοσης
09/07/2026 3:54 μ . μ .
Στοιχεία  Πελάτη
ΑΦΜ802313849
Ανάλυση
ΚωδικόςΠεριγραφή ΠοσότηταM.M.
Φ . Π . ΑΤελικό
P01946 2447 - Fixed 24 - 1 x Lenovo ThinkPad L16 Gen2 CoreUltra5 32GB | 1TB (at
€54.16 / month)
1,00Τεμάχια 54,16 0,00 0,00 54,16 24 13,00 67,16
Εκπτώσεις / Χρεώσεις
Ανάλυση  ΦΠΑ
24,00% 54,16 13,00
Νόμισμα EUR
Σύνολο  Καθαρού  Ποσού 54,16
Σύνολο  Φ . Π . Α 13,00
Συνολική  Αξία 67,16
Σχόλια  FINCO2-0988
"""

FINLOUP_STRIPE_TEXT = """\xa0
Τɩμολόγɩο
Αρɩθμός τɩμολογίου FINCO1\x0016086
Ημερομηνία έκδοσης 6 Ιουλίου 2026
Finloup Leasing I
GR VAT EL802285336
Χρέωση σε
GR VAT EL802313849
36,51\xa0€ πληρωτέο στɩς 6 Ιουλίου 2026
Περɩγραφή Ποσότητα
Samsung Galaxy S25
6 Ιουλ 2026\x006 Αυγ 2026
1 29,44\xa0€ 24% 29,44\xa0€
\xa0
Μερɩκό σύνολο 29,44\xa0€
Σύνολο χωρίς φόρο 29,44\xa0€
VAT - Greece \x0024% επί του ποσού 29,44\xa0€\x00 7,07\xa0€
Σύνολο 36,51\xa0€
Πληρωτέο ποσό 36,51\xa0€
"""


def test_parse_finloup_einvoice_leasing2() -> None:
    parser = FinloupLeasing2Parser()
    normalized = FINLOUP_EINVOICE_TEXT.replace(" ", "").upper()
    assert parser.matches(normalized)
    assert not FinloupLeasing1Parser().matches(normalized)
    invoice = parser.parse_text(Path("finloup.pdf"), FINLOUP_EINVOICE_TEXT)
    assert invoice.supplier_vat == "803183981"
    assert invoice.document_number == "988"
    assert invoice.document_date == date(2026, 7, 9)
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal("54.16"),
        Decimal("13.00"),
        Decimal("67.16"),
    )
    assert invoice.vat_pct == Decimal("24")
    assert [(line.code, line.value, line.vat_pct) for line in invoice.lines] == [
        ("P01946", Decimal("54.16"), Decimal("24"))
    ]
    assert invoice.description == "ΜΙΣΘΩΜΑ LENOVO THINKPAD L16 GEN2 COREULTRA5 32GB | 1TB"


def test_parse_finloup_stripe_leasing1() -> None:
    parser = FinloupLeasing1Parser()
    normalized = FINLOUP_STRIPE_TEXT.replace(" ", "").upper()
    assert parser.matches(normalized)
    assert not FinloupLeasing2Parser().matches(normalized)
    invoice = parser.parse_text(Path("finloup.pdf"), FINLOUP_STRIPE_TEXT)
    assert invoice.supplier_vat == "802285336"
    assert invoice.document_number == "16086"
    assert invoice.document_date == date(2026, 7, 6)
    assert (invoice.net_value, invoice.vat_value, invoice.total_value) == (
        Decimal("29.44"),
        Decimal("7.07"),
        Decimal("36.51"),
    )
    assert invoice.vat_pct == Decimal("24")
    assert [line.value for line in invoice.lines] == [Decimal("29.44")]
    assert invoice.description == "ΜΙΣΘΩΜΑ SAMSUNG GALAXY S25 (6 ΙΟΥΛ 2026 - 6 ΑΥΓ 2026)"


def test_finloup_rejects_total_mismatch() -> None:
    text = FINLOUP_EINVOICE_TEXT.replace("Συνολική  Αξία 67,16", "Συνολική  Αξία 68,16")
    with pytest.raises(PdfParseError):
        FinloupLeasing2Parser().parse_text(Path("finloup.pdf"), text)


def test_finloup_rejects_lines_not_matching_net() -> None:
    text = FINLOUP_STRIPE_TEXT.replace("1 29,44\xa0€ 24% 29,44\xa0€", "1 29,44\xa0€ 24% 19,44\xa0€")
    with pytest.raises(PdfParseError, match="γραμμές"):
        FinloupLeasing1Parser().parse_text(Path("finloup.pdf"), text)


def test_finloup_rejects_non_invoice_kind() -> None:
    text = FINLOUP_EINVOICE_TEXT.replace(
        "Τιμολόγιο  Παροχής  Υπηρεσιών", "Πιστωτικό  Τιμολόγιο  Παροχής  Υπηρεσιών"
    )
    with pytest.raises(PdfParseError, match="Πιστωτικό"):
        FinloupLeasing2Parser().parse_text(Path("finloup.pdf"), text)
