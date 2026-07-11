from __future__ import annotations

import argparse
import json
import sys

from softone_pilot.audit import write_dry_run_audit
from softone_pilot.automation import SoftOneAutomationError, inspect_softone_controls
from softone_pilot.config import default_config, load_config
from softone_pilot.parsers import parse_pdf
from softone_pilot.parsers.base import PdfParseError
from softone_pilot.planner import collect_pdfs, dry_run_steps, prepare_batch


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
    dry_run.add_argument("--audit", default="pilot-data/audit.jsonl")
    dry_run.add_argument("--no-audit", action="store_true")
    dry_run.add_argument("--json", action="store_true")

    inspect = commands.add_parser(
        "inspect-softone",
        help="Read-only καταγραφή UI Automation controls",
    )
    inspect.add_argument("--workflow", required=True)
    inspect.add_argument("--output", default="softone_controls.txt")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "parse":
        _parse(args)
    elif args.command == "dry-run":
        _dry_run(args)
    elif args.command == "inspect-softone":
        _inspect(args)


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
    if not args.no_audit:
        try:
            write_dry_run_audit(args.audit, prepared, parse_errors)
        except OSError as exc:
            print(f"WARNING: Το audit log δεν γράφτηκε: {exc}", file=sys.stderr)
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


if __name__ == "__main__":
    main()
