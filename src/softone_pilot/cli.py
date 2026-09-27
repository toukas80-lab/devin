from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal

from softone_pilot.automation import SoftOneAutomationError, inspect_softone_controls
from softone_pilot.config import default_config, load_config
from softone_pilot.parsers import parse_pdf
from softone_pilot.parsers.base import PdfParseError
from softone_pilot.planner import collect_pdfs, dry_run_steps, prepare_batch
from softone_pilot.sql_readonly import SoftOneReadOnlyRepository, SqlReadOnlyError
from softone_pilot.valuation import ValuationAssumptions, compute_valuation, format_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SoftOne PDF desktop pilot")
    commands = parser.add_subparsers(dest="command", required=True)

    parse_command = commands.add_parser("parse", help="Ανάλυση ενός text PDF")
    parse_command.add_argument("pdf")
    parse_command.add_argument("--json", action="store_true")

    dry_run = commands.add_parser("dry-run", help="Batch preview χωρίς καταχώριση")
    dry_run.add_argument("path", help="PDF ή φάκελος PDF")
    dry_run.add_argument("--config")
    dry_run.add_argument("--no-sql", action="store_true")
    dry_run.add_argument("--json", action="store_true")

    inspect = commands.add_parser(
        "inspect-softone",
        help="Read-only καταγραφή UI Automation controls",
    )
    inspect.add_argument("--workflow", required=True)
    inspect.add_argument("--output", default="softone_controls.txt")

    valuation = commands.add_parser(
        "valuation",
        help="Read-only αποτίμηση εταιρίας από ιστορικό SoftOne",
    )
    valuation.add_argument("--config", required=True)
    valuation.add_argument("--years", type=int, default=6)
    valuation.add_argument("--multiples", default="3,4,5", help="EBITDA low,mid,high")
    valuation.add_argument("--discount-rate", type=Decimal, default=Decimal("0.12"))
    valuation.add_argument("--longevity-premium", type=Decimal, default=Decimal("0.10"))
    valuation.add_argument(
        "--opex-ratio",
        type=Decimal,
        help="Λειτουργικά έξοδα ως ποσοστό πωλήσεων όταν δεν υπάρχει Γενική Λογιστική",
    )
    valuation.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "parse":
        _parse(args)
    elif args.command == "dry-run":
        _dry_run(args)
    elif args.command == "inspect-softone":
        _inspect(args)
    elif args.command == "valuation":
        _valuation(args)


def _parse(args) -> None:
    try:
        invoice = parse_pdf(args.pdf)
    except PdfParseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.json:
        print(json.dumps(invoice.to_dict(), ensure_ascii=False, indent=2))
    else:
        for key, value in invoice.to_dict().items():
            print(f"{key}: {value}")


def _dry_run(args) -> None:
    config = load_config(args.config) if args.config else default_config()
    pdfs = collect_pdfs(args.path)
    if not pdfs:
        print("ERROR: Δεν βρέθηκαν PDF", file=sys.stderr)
        raise SystemExit(1)

    prepared, parse_errors = prepare_batch(pdfs, config, use_sql=not args.no_sql)
    payload = {
        "items": [item.to_dict() for item in prepared],
        "parse_errors": parse_errors,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return

    for item in prepared:
        status = "READY" if item.ready else "BLOCKED"
        print(f"\n[{status}] {item.invoice.source_path.name}")
        for error in item.errors:
            print(f"  ERROR: {error}")
        for warning in item.warnings:
            print(f"  WARNING: {warning}")
        for step in dry_run_steps(item):
            print(f"  - {step}")
    for error in parse_errors:
        print(f"\nPARSE ERROR: {error}")


def _inspect(args) -> None:
    try:
        output = inspect_softone_controls(args.workflow, args.output)
    except SoftOneAutomationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(output.resolve())


def _valuation(args) -> None:
    config = load_config(args.config)
    try:
        low, mid, high = (Decimal(part) for part in args.multiples.split(","))
    except ValueError as exc:
        print("ERROR: --multiples πρέπει να είναι low,mid,high", file=sys.stderr)
        raise SystemExit(1) from exc
    assumptions = ValuationAssumptions(
        multiple_low=low,
        multiple_mid=mid,
        multiple_high=high,
        discount_rate=args.discount_rate,
        longevity_premium=args.longevity_premium,
        opex_ratio=args.opex_ratio,
    )
    try:
        with SoftOneReadOnlyRepository(config.sql) as repo:
            years = repo.fiscal_years(args.years)
            if not years:
                print("ERROR: Δεν βρέθηκαν οικονομικές χρήσεις", file=sys.stderr)
                raise SystemExit(1)
            figures = repo.yearly_figures(years)
            balance = repo.balance_snapshot(years[-1])
    except SqlReadOnlyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    result = compute_valuation(figures, balance, assumptions)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_report(result))


if __name__ == "__main__":
    main()
