from __future__ import annotations

from softone_pilot.parsers.cargobook import CargoBookParser


class HellenicShippingParser(CargoBookParser):
    """ΕΛΛΗΝΙΚΑ ΝΑΥΤΙΚΑ ΠΡΑΚΤΟΡΕΙΑ ΕΠΕ (HELLENIC SHIPPING AGENCIES) depot/warehouse invoice.

    Same invoicing layout as CARGO BOOK: charge lines carry a charge code (``5586-19``...) used as
    category for ``line_codes``."""

    vat = "095082846"
    name = "ΕΛΛΗΝΙΚΑ ΝΑΥΤΙΚΑ ΠΡΑΚΤΟΡΕΙΑ ΕΠΕ"
