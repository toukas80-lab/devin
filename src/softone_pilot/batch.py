from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from softone_pilot.automation import (
    SoftOneAutomationError,
    build_invoice_context,
    execute_profile,
    launch_softone,
)
from softone_pilot.config import AppConfig
from softone_pilot.credentials import CredentialStoreError, read_windows_credential
from softone_pilot.models import PreparedInvoice


@dataclass(frozen=True)
class BatchItemResult:
    source_path: Path
    profile: str
    executed_steps: tuple[str, ...]
    saved: bool
    save_skipped: bool
    error: str = ""


@dataclass(frozen=True)
class BatchExecution:
    launched: bool
    results: tuple[BatchItemResult, ...]
    stopped_early: bool


def execute_batch(
    items: list[PreparedInvoice],
    config: AppConfig,
    workflow_path: str | Path,
    *,
    allow_save: bool = False,
    continue_on_error: bool = False,
) -> BatchExecution:
    settings = config.automation
    if not settings.enabled:
        raise SoftOneAutomationError("Η πλήρης αυτοματοποίηση είναι απενεργοποιημένη")
    if not items:
        raise SoftOneAutomationError("Δεν υπάρχουν έτοιμα PDF για εκτέλεση")

    launch = launch_softone(
        workflow_path,
        settings.startup_profile,
        settings.executable_path,
        settings.arguments,
        timeout_seconds=settings.startup_timeout_seconds,
    )
    startup_context = _credential_context(settings.credential_target)
    execute_profile(
        workflow_path,
        settings.startup_profile,
        startup_context,
        process_id=launch.process_id,
    )

    results: list[BatchItemResult] = []
    stopped_early = False
    for item in items:
        profile = item.settings.workflow_profile if item.settings else ""
        context = build_invoice_context(item)
        try:
            if settings.navigation_profile:
                execute_profile(
                    workflow_path,
                    settings.navigation_profile,
                    context,
                )
            execution = execute_profile(
                workflow_path,
                profile,
                context,
                allow_save=allow_save,
            )
            saved = allow_save and execution.saved
            results.append(
                BatchItemResult(
                    source_path=item.invoice.source_path,
                    profile=profile,
                    executed_steps=execution.executed_steps,
                    saved=saved,
                    save_skipped=execution.save_skipped,
                )
            )
            if saved:
                _move_processed(
                    item.invoice.source_path,
                    Path(settings.processed_path),
                )
            else:
                stopped_early = True
                break
        except SoftOneAutomationError as exc:
            results.append(
                BatchItemResult(
                    source_path=item.invoice.source_path,
                    profile=profile,
                    executed_steps=(),
                    saved=False,
                    save_skipped=False,
                    error=str(exc),
                )
            )
            if not continue_on_error:
                stopped_early = True
                break

    return BatchExecution(
        launched=launch.launched,
        results=tuple(results),
        stopped_early=stopped_early,
    )


def _credential_context(target: str) -> dict[str, str]:
    try:
        credential = read_windows_credential(target)
    except CredentialStoreError:
        return {"username": "", "password": ""}
    return {
        "username": credential.username,
        "password": credential.password,
    }


def _move_processed(source: Path, processed_directory: Path) -> Path:
    processed_directory.mkdir(parents=True, exist_ok=True)
    target = processed_directory / source.name
    if target.exists():
        raise SoftOneAutomationError(f"Υπάρχει ήδη επεξεργασμένο PDF: {target}")
    shutil.move(str(source), target)
    return target
