from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from softone_pilot import cli
from softone_pilot.automation import SoftOneAutomationError


def test_audit_failure_does_not_hide_cli_results(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "collect_pdfs", lambda path: [Path("invoice.pdf")])
    monkeypatch.setattr(cli, "prepare_batch", lambda pdfs, config, use_sql: ([], []))

    def fail_audit(path, prepared, parse_errors):
        raise OSError("disk full")

    monkeypatch.setattr(cli, "write_dry_run_audit", fail_audit)
    cli._dry_run(
        Namespace(
            path="invoice.pdf",
            config=None,
            no_sql=True,
            no_audit=False,
            audit="audit.jsonl",
            json=True,
        )
    )

    output = capsys.readouterr()
    assert '"items": []' in output.out
    assert "audit log" in output.err


def test_workflow_rejects_multiple_pdfs_with_an_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "collect_pdfs", lambda path: [Path("a.pdf"), Path("b.pdf")])
    monkeypatch.setattr(
        cli,
        "prepare_batch",
        lambda pdfs, config, use_sql: ([object(), object()], []),
    )

    with pytest.raises(SystemExit):
        cli._workflow(
            Namespace(
                pdf="invoices",
                config=None,
                workflow="workflow.json",
                profile="creditor_expense.create",
                no_sql=True,
                execute=False,
                allow_save=False,
            )
        )

    assert "Αναμένεται ένα PDF, βρέθηκαν 2" in capsys.readouterr().err


def test_batch_preview_reports_clean_workflow_error(monkeypatch, capsys) -> None:
    config = SimpleNamespace(
        automation=SimpleNamespace(
            inbox_path="inbox",
            startup_profile="softone.login",
            navigation_profile="creditor_expense.open_create",
        )
    )
    item = SimpleNamespace(
        ready=True,
        invoice=SimpleNamespace(source_path=Path("invoice.pdf")),
        settings=SimpleNamespace(workflow_profile="creditor_expense.create"),
    )
    monkeypatch.setattr(cli, "load_config", lambda path: config)
    monkeypatch.setattr(cli, "collect_pdfs", lambda path: [Path("invoice.pdf")])
    monkeypatch.setattr(cli, "prepare_batch", lambda pdfs, config, use_sql: ([item], []))
    monkeypatch.setattr(
        cli,
        "preview_workflow",
        lambda workflow, profile, item: (_ for _ in ()).throw(
            SoftOneAutomationError("λείπει SQL supplier")
        ),
    )

    with pytest.raises(SystemExit):
        cli._batch(
            Namespace(
                path=None,
                config="config.json",
                workflow="workflow.json",
                no_sql=True,
                execute=False,
                allow_save=False,
                continue_on_error=False,
                audit="audit.jsonl",
                no_audit=True,
            )
        )

    assert "ERROR: λείπει SQL supplier" in capsys.readouterr().err
