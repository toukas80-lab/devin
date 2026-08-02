"""Convert a FedEx PDF invoice into a SoftOne XXF file."""

from __future__ import annotations

import argparse
from pathlib import Path

from pdf2xxf import fedex, generator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="FedEx invoice PDF")
    parser.add_argument("--template", required=True, help="XXF exported from SoftOne")
    parser.add_argument("--out", help="output XXF (defaults to <invoice number>.XXF)")
    parser.add_argument(
        "--keep-series-number",
        action="store_true",
        help="keep the template's SERIESNUM instead of letting SoftOne assign one",
    )
    args = parser.parse_args(argv)

    invoice = fedex.parse_pdf(args.pdf)
    xxf = generator.build(
        Path(args.template).read_bytes(),
        invoice,
        reset_series=not args.keep_series_number,
    )
    out = Path(args.out or f"{invoice.number}.XXF")
    out.write_bytes(xxf)

    print(f"{invoice.number}  {invoice.date:%d/%m/%Y}  {len(invoice.shipments)} αποστολές")
    print(f"καθαρή {invoice.net:.2f}  ΦΠΑ {invoice.vat:.2f}  σύνολο {invoice.total:.2f}")
    checked = round(invoice.net + invoice.vat, 2)
    if abs(checked - invoice.total) > 0.01:
        print(f"ΠΡΟΣΟΧΗ: καθαρή+ΦΠΑ = {checked:.2f} αλλά το τιμολόγιο λέει {invoice.total:.2f}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
