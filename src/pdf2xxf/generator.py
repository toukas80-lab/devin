"""Build a SoftOne purchase document (XXF) for a FedEx invoice.

A real SoftOne export of the same document type is used as the template: its
records are rewritten field by field through the codec, so lengths, offsets and
the packet framing are always recomputed instead of patched.
"""

from __future__ import annotations

import copy
import datetime

from pdf2xxf import codec, values
from pdf2xxf.fedex import Invoice, Shipment

FINDOC_PACKET = "#STDLINCREDOC.FINDOC"
MTRDOC_PACKET = "#STDLINCREDOC.MTRDOC"
LINES_PACKET = "#STDLINCREDOC.MTRLINES"
VATANAL_PACKET = "#STDLINCREDOC.VATANAL"
PAYTERMS_PACKET = "#STDLINCREDOC.FINPAYTERMS"

SERIES_PREFIX = "ΤΙΜΔ"
VAT_CODE_STANDARD = 1410
VAT_CODE_ZERO = 0

# SoftOne item used for each kind of FedEx charge.
ITEM_EXPORT_TAXED = "10016"
ITEM_EXPORT_EXEMPT = "10017"
ITEM_IMPORT = "10002"


def item_code(shipment: Shipment) -> str:
    if not shipment.is_export:
        return ITEM_IMPORT
    return ITEM_EXPORT_TAXED if shipment.vat_rate else ITEM_EXPORT_EXEMPT


def build(template: bytes, invoice: Invoice, reset_series: bool = True) -> bytes:
    doc = codec.parse(template)
    _fill_header(doc, invoice, reset_series)
    _fill_lines(doc, invoice)
    _fill_vat_analysis(doc, invoice)
    _fill_payment(doc, invoice)
    return codec.serialize(doc)


def _fill_header(doc: codec.Document, invoice: Invoice, reset_series: bool) -> None:
    p = doc.packet(FINDOC_PACKET)
    date = datetime.datetime.combine(invoice.date, datetime.time())
    for name in ("TRNDATE", "BGDOCDATE", "BGDOCDATE1"):
        values.put(p, 0, name, date)
    values.put(p, 0, "PERIOD", invoice.date.month)
    values.put(p, 0, "FISCPRD", invoice.date.year)
    values.put(p, 0, "TAXSERIESNUM", invoice.number)
    values.put(p, 0, "FINCODE", f"{SERIES_PREFIX}-{invoice.number}")
    values.put(p, 0, "COMMENTS", _comments(invoice))
    if reset_series:
        values.put(p, 0, "SERIESNUM", 0)

    net, vat, total = invoice.net, invoice.vat, invoice.total
    for name in ("TURNOVR", "TTURNOVR", "LTURNOVR", "NETAMNT", "TNETAMNT", "LNETAMNT"):
        values.put(p, 0, name, net)
    for name in ("VATAMNT", "TVATAMNT", "LVATAMNT"):
        values.put(p, 0, name, vat)
    for name in ("SUMAMNT", "SUMTAMNT", "SUMLAMNT"):
        values.put(p, 0, name, total)
    values.put(p, 0, "LKEPYOVAL", net)

    domestic = [s for s in invoice.shipments if not s.is_export]
    values.put(p, 0, "GSISNET", round(sum(s.amount for s in domestic), 2))
    values.put(
        p, 0, "GSISVAT", round(sum(s.amount * s.vat_rate / 100 for s in domestic), 2)
    )
    values.put(p, 0, "GSISPACKAGES", len(invoice.shipments) - len(domestic))


def _comments(invoice: Invoice) -> str:
    return " / ".join(s.number for s in invoice.shipments)


def _fill_lines(doc: codec.Document, invoice: Invoice) -> None:
    p = doc.packet(LINES_PACKET)
    templates = {values.get(p, i, "MTRL_CODE"): p.records[i] for i in range(len(p.records))}
    comments = _comments(invoice)
    records = []
    for number, shipment in enumerate(invoice.shipments, start=1):
        code = item_code(shipment)
        if code not in templates:
            raise ValueError(f"the template has no line for item {code}")
        record = copy.deepcopy(templates[code])
        record.row = number
        p.records = [record]
        vat = round(shipment.amount * shipment.vat_rate / 100, 2)
        values.put(p, 0, "LINENUM", number)
        values.put(p, 0, "MTRLINES", number)
        values.put(p, 0, "COMMENTS", comments)
        for name in ("LINEVAL", "LLINEVAL", "NETLINEVAL", "LNETLINEVAL",
                     "TRNLINEVAL", "LTRNLINEVAL"):
            values.put(p, 0, name, shipment.amount)
        for name in ("VATAMNT", "LVATAMNT"):
            values.put(p, 0, name, vat)
        values.put(p, 0, "VAT", VAT_CODE_STANDARD if shipment.vat_rate else VAT_CODE_ZERO)
        records.append(record)
    p.records = records


def _fill_vat_analysis(doc: codec.Document, invoice: Invoice) -> None:
    p = doc.packet(VATANAL_PACKET)
    by_rate: dict[float, list[Shipment]] = {}
    for shipment in invoice.shipments:
        by_rate.setdefault(shipment.vat_rate, []).append(shipment)
    templates = {values.get(p, i, "VAT"): p.records[i] for i in range(len(p.records))}
    records = []
    for number, (rate, shipments) in enumerate(sorted(by_rate.items()), start=1):
        vat_code = VAT_CODE_STANDARD if rate else VAT_CODE_ZERO
        if vat_code not in templates:
            raise ValueError(f"the template has no VAT analysis row for {rate}%")
        record = copy.deepcopy(templates[vat_code])
        record.row = number
        p.records = [record]
        net = round(sum(s.amount for s in shipments), 2)
        values.put(p, 0, "LINENUM", number)
        values.put(p, 0, "VAT", vat_code)
        values.put(p, 0, "SUBVAL", net)
        values.put(p, 0, "LSUBVAL", net)
        values.put(p, 0, "VATVAL", round(net * rate / 100, 2))
        values.put(p, 0, "LVATVAL", round(net * rate / 100, 2))
        records.append(record)
    p.records = records


def _fill_payment(doc: codec.Document, invoice: Invoice) -> None:
    p = doc.packet(PAYTERMS_PACKET)
    if not p.records:
        return
    values.put(p, 0, "TRNDATE", datetime.datetime.combine(invoice.date, datetime.time()))
    values.put(
        p, 0, "FINALDATE", datetime.datetime.combine(invoice.due_date, datetime.time())
    )
    for name in ("AMNT", "TAMNT", "LAMNT", "OPNTAMNT"):
        values.put(p, 0, name, invoice.total)
    values.put(p, 0, "COMMENTS", f"{SERIES_PREFIX}-{invoice.number}")
