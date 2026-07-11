from __future__ import annotations

import argparse
import getpass
import json
import sys

from softone_pilot.audit import write_batch_audit, write_dry_run_audit
from softone_pilot.automation import (
    SoftOneAutomationError,
    execute_workflow,
    inspect_softone_controls,
    preview_workflow,
)
from softone_pilot.batch import execute_batch
from softone_pilot.config import default_config, load_config
from softone_pilot.credentials import CredentialStoreError, write_windows_credential
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

    workflow = commands.add_parser(
        "workflow",
        help="Preview ή εκτέλεση παραμετρικής ροής SoftOne",
    )
    workflow.add_argument("pdf")
    workflow.add_argument("--config")
    workflow.add_argument("--workflow", default="config/softone_workflow.example.json")
    workflow.add_argument("--profile", default="creditor_expense.create")
    workflow.add_argument("--no-sql", action="store_true")
    workflow.add_argument("--execute", action="store_true")
    workflow.add_argument("--allow-save", action="store_true")

    batch = commands.add_parser(
        "batch",
        help="Πλήρης ροή φακέλου PDF με αυτόματη εκκίνηση SoftOne",
    )
    batch.add_argument("path", nargs="?")
    batch.add_argument("--config", required=True)
    batch.add_argument("--workflow", default="config/softone_workflow.example.json")
    batch.add_argument("--no-sql", action="store_true")
    batch.add_argument("--execute", action="store_true")
    batch.add_argument("--allow-save", action="store_true")
    batch.add_argument("--continue-on-error", action="store_true")
    batch.add_argument("--audit", default="pilot-data/batch-audit.jsonl")
    batch.add_argument("--no-audit", action="store_true")

    credentials = commands.add_parser(
        "store-credentials",
        help="Αποθήκευση SoftOne login στο Windows Credential Manager",
    )
    credentials.add_argument("--config", required=True)
    credentials.add_argument("--username", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "parse":
        _parse(args)
    elif args.command == "dry-run":
        _dry_run(args)
    elif args.command == "inspect-softone":
        _inspect(args)
    elif args.command == "workflow":
        _workflow(args)
    elif args.command == "batch":
        _batch(args)
    elif args.command == "store-credentials":
        _store_credentials(args)


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


def _workflow(args) -> None:
    if args.allow_save and not args.execute:
        print("ERROR: Το --allow-save απαιτεί --execute", file=sys.stderr)
        raise SystemExit(2)

    config = load_config(args.config) if args.config else default_config()
    prepared, parse_errors = prepare_batch(
        collect_pdfs(args.pdf),
        config,
        use_sql=not args.no_sql,
    )
    if parse_errors or len(prepared) != 1:
        for error in parse_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if not prepared:
            print("ERROR: Δεν προετοιμάστηκε παραστατικό", file=sys.stderr)
        elif len(prepared) > 1:
            print(f"ERROR: Αναμένεται ένα PDF, βρέθηκαν {len(prepared)}", file=sys.stderr)
        raise SystemExit(1)

    item = prepared[0]
    if not item.ready:
        for error in item.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    try:
        preview = preview_workflow(args.workflow, args.profile, item)
        payload = {"profile": args.profile, "steps": preview, "executed": False}
        if args.execute:
            result = execute_workflow(
                args.workflow,
                args.profile,
                item,
                allow_save=args.allow_save,
            )
            payload.update(
                {
                    "executed": True,
                    "executed_steps": list(result.executed_steps),
                    "save_skipped": result.save_skipped,
                }
            )
    except SoftOneAutomationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _batch(args) -> None:
    if args.allow_save and not args.execute:
        print("ERROR: Το --allow-save απαιτεί --execute", file=sys.stderr)
        raise SystemExit(2)

    config = load_config(args.config)
    source = args.path or config.automation.inbox_path
    pdfs = collect_pdfs(source)
    if not pdfs:
        print(f"ERROR: Δεν βρέθηκαν PDF στο {source}", file=sys.stderr)
        raise SystemExit(1)

    prepared, parse_errors = prepare_batch(
        pdfs,
        config,
        use_sql=not args.no_sql,
    )
    blocked = [item for item in prepared if not item.ready]
    if parse_errors or blocked:
        for error in parse_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for item in blocked:
            for error in item.errors:
                print(f"ERROR: {item.invoice.source_path.name}: {error}", file=sys.stderr)
        raise SystemExit(1)

    if not args.execute:
        try:
            payload = {
                "source": str(source),
                "startup_profile": config.automation.startup_profile,
                "navigation_profile": config.automation.navigation_profile,
                "items": [
                    {
                        "pdf": str(item.invoice.source_path),
                        "profile": item.settings.workflow_profile if item.settings else "",
                        "steps": preview_workflow(
                            args.workflow,
                            item.settings.workflow_profile if item.settings else "",
                            item,
                        ),
                    }
                    for item in prepared
                ],
                "executed": False,
            }
        except SoftOneAutomationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    try:
        result = execute_batch(
            prepared,
            config,
            args.workflow,
            allow_save=args.allow_save,
            continue_on_error=args.continue_on_error,
        )
    except SoftOneAutomationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    payload = {
        "executed": True,
        "launched": result.launched,
        "stopped_early": result.stopped_early,
        "items": [
            {
                "pdf": str(item.source_path),
                "profile": item.profile,
                "executed_steps": list(item.executed_steps),
                "saved": item.saved,
                "save_skipped": item.save_skipped,
                "error": item.error,
            }
            for item in result.results
        ],
    }
    if not args.no_audit:
        try:
            write_batch_audit(args.audit, result)
        except OSError as exc:
            print(f"WARNING: Το audit log δεν γράφτηκε: {exc}", file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if any(item.error for item in result.results):
        raise SystemExit(1)


def _store_credentials(args) -> None:
    config = load_config(args.config)
    password = getpass.getpass("SoftOne password: ")
    try:
        write_windows_credential(
            config.automation.credential_target,
            args.username,
            password,
        )
    except CredentialStoreError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("Τα στοιχεία αποθηκεύτηκαν στο Windows Credential Manager")


if __name__ == "__main__":
    main()
