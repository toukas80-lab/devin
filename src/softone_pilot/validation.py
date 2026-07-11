from __future__ import annotations

from decimal import Decimal

from softone_pilot.models import InvoiceData, SupplierSettings


def validate_invoice(
    invoice: InvoiceData,
    settings: SupplierSettings | None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not invoice.document_number.strip():
        errors.append("Δεν υπάρχει αριθμός παραστατικού")
    if invoice.net_value <= Decimal("0"):
        errors.append("Η καθαρή αξία πρέπει να είναι θετική")
    if invoice.vat_value < Decimal("0"):
        errors.append("Ο ΦΠΑ δεν μπορεί να είναι αρνητικός")
    if invoice.total_value <= Decimal("0"):
        errors.append("Το σύνολο πρέπει να είναι θετικό")
    if abs(invoice.net_value + invoice.vat_value - invoice.total_value) > Decimal("0.02"):
        errors.append("Καθαρή αξία + ΦΠΑ δεν συμφωνούν με το σύνολο")
    if settings is None:
        errors.append("Δεν υπάρχει τοπική αντιστοίχιση SoftOne για τον εκδότη")
    elif not settings.is_complete:
        errors.append("Η αντιστοίχιση σειράς/γραμμής/πληρωμής δεν έχει ολοκληρωθεί")

    return errors, warnings
