from pdf2xxf import fedex

SAMPLE = """
Αριθμός τιμολογίου:
Ημερομηνία τιμολογίου:
Προς πληρωμή:
685258118
28/07/2026
27/08/2026
Αρ. Αποστολής Ημερομηνία
46.1415/07/2026874406506564 0.00 46.14FedEx Regional Economy
198.90Αποστολέας Παραλήπτης Χρέωση Μεταφορικών
-161.39FOUNTOUKAS THEODOROS VN FOOD PROCESSING EQUIPMENT Εκπτωση
Υποσύνολο EURV.ITILEA 21/07/2026 16:23Υπογραφή: 46.14
Ισχύον ΦΠΑ 24.00%
Αρ. Αποστολής Ημερομηνία
11.8813/07/2026874266670131 0.00 11.88FedEx Regional Economy
63.85Αποστολέας Παραλήπτης Χρέωση Μεταφορικών
-54.19AGNIESZKA URBANIAK ORAIOKASTRO, GREECE Εκπτωση
Υποσύνολο EURF.FOUNTOUKAS 20/07/2026 12:10Υπογραφή: 11.88
Ισχύον ΦΠΑ 24.00%
Συνολική Αξία EUR 58.02
"""


def test_parses_header_and_shipments():
    invoice = fedex.parse_text(SAMPLE)
    assert invoice.number == "685258118"
    assert invoice.date.isoformat() == "2026-07-28"
    assert invoice.due_date.isoformat() == "2026-08-27"
    assert invoice.total == 58.02
    assert [s.number for s in invoice.shipments] == ["874406506564", "874266670131"]
    assert invoice.net == 58.02
    assert invoice.vat == 13.92


def test_direction_follows_the_sender():
    invoice = fedex.parse_text(SAMPLE)
    assert invoice.shipments[0].is_export
    assert not invoice.shipments[1].is_export


def test_invoice_vat_is_the_sum_of_the_line_amounts():
    shipments = [fedex.Shipment(str(i), 10.05, 24.0, "X") for i in range(3)]
    invoice = fedex.Invoice("1", None, None, 37.39, shipments)
    assert invoice.vat == round(sum(s.vat for s in shipments), 2)
