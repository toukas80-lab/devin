from argparse import Namespace
from pathlib import Path

import pytest

from softone_pilot import cli


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
