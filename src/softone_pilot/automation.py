from __future__ import annotations

import json
import platform
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from string import Formatter

from softone_pilot.models import PreparedInvoice

if platform.system() == "Windows":
    from pywinauto import Desktop, keyboard
else:
    Desktop = None
    keyboard = None


class SoftOneAutomationError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkflowExecution:
    profile: str
    executed_steps: tuple[str, ...]
    save_skipped: bool
    saved: bool = False
    screenshot: Path | None = None


@dataclass(frozen=True)
class SoftOneLaunch:
    launched: bool
    process_id: int | None = None


def inspect_softone_controls(workflow_path: str | Path, output_path: str | Path) -> Path:
    desktop = _windows_desktop()
    workflow = _load_workflow(workflow_path)
    window = _find_window(desktop, workflow["window"])

    target = Path(output_path)
    with target.open("w", encoding="utf-8") as handle:
        handle.write(f"Window: {window.window_text()}\n")
        for control in window.descendants():
            info = control.element_info
            handle.write(
                " | ".join(
                    (
                        f"title={info.name!r}",
                        f"auto_id={info.automation_id!r}",
                        f"type={info.control_type!r}",
                        f"class={info.class_name!r}",
                    )
                )
                + "\n"
            )
    return target


def validate_workflow_profile(
    workflow_path: str | Path,
    profile_name: str | None = None,
) -> list[str]:
    workflow = _load_workflow(workflow_path)
    errors: list[str] = []
    window = workflow.get("window")
    if not isinstance(window, dict) or not _selector_has_identity(window):
        errors.append("window")

    profiles = workflow.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        return [*errors, "profiles"]

    selected = {profile_name: profiles.get(profile_name)} if profile_name else profiles
    for name, profile in selected.items():
        if not isinstance(profile, dict):
            errors.append(f"profiles.{name}")
            continue
        if profile.get("operation") not in {
            "cancel",
            "create",
            "edit",
            "login",
            "navigate",
            "transform",
        }:
            errors.append(f"profiles.{name}.operation")
        profile_window = profile.get("window")
        if profile_window is not None and (
            not isinstance(profile_window, dict)
            or not _selector_has_identity(profile_window)
        ):
            errors.append(f"profiles.{name}.window")
        steps = profile.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"profiles.{name}.steps")
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"profiles.{name}.steps.{index}")
                continue
            action = step.get("action")
            if action not in {
                "assert",
                "assert_absent",
                "click",
                "grid_set",
                "press_keys",
                "save",
                "set",
                "switch_window",
                "type_focused",
                "wait_absent",
                "wait_present",
            }:
                errors.append(f"profiles.{name}.steps.{index}.action")
            if action in {
                "assert",
                "assert_absent",
                "click",
                "save",
                "set",
                "switch_window",
                "wait_absent",
                "wait_present",
            }:
                selector = step.get("selector")
                if not isinstance(selector, dict) or not _selector_has_identity(selector):
                    errors.append(f"profiles.{name}.steps.{index}.selector")
            if action == "press_keys" and not step.get("keys"):
                errors.append(f"profiles.{name}.steps.{index}.keys")
            if action == "grid_set":
                for key in ("grid", "column"):
                    selector = step.get(key)
                    if not isinstance(selector, dict) or not _selector_has_identity(selector):
                        errors.append(f"profiles.{name}.steps.{index}.{key}")
    return errors


def commit_is_available(
    workflow_path: str | Path,
    profile_name: str | None = None,
) -> bool:
    if validate_workflow_profile(workflow_path, profile_name):
        return False
    workflow = _load_workflow(workflow_path)
    profiles = workflow["profiles"]
    selected = [profiles[profile_name]] if profile_name else profiles.values()
    transactional = [
        profile
        for profile in selected
        if profile.get("operation") not in {"login", "navigate"}
    ]
    return all(
        any(step.get("action") == "save" for step in profile["steps"])
        for profile in transactional
    )


def build_invoice_context(item: PreparedInvoice) -> dict[str, str]:
    if not item.ready:
        raise SoftOneAutomationError("Το παραστατικό είναι BLOCKED και δεν μπορεί να εκτελεστεί")
    if item.settings is None or item.sql_supplier is None:
        raise SoftOneAutomationError("Λείπει αντιστοίχιση προμηθευτή ή SoftOne ρυθμίσεων")

    invoice = item.invoice
    settings = item.settings
    return {
        "source_filename": invoice.source_path.name,
        "supplier_code": item.sql_supplier.code,
        "supplier_name": item.sql_supplier.name,
        "supplier_vat": invoice.supplier_vat,
        "series_code": settings.series_code,
        "line_code": settings.line_code,
        "payment_method": settings.payment_method,
        "workflow_profile": settings.workflow_profile,
        "company_branch": settings.company_branch,
        "supplier_branch": settings.supplier_branch,
        "warehouse": settings.warehouse,
        "document_type": settings.document_type,
        "vat_regime": settings.vat_regime,
        "quantity": settings.quantity,
        "unit_price": _format_amount(invoice.net_value),
        "discount": settings.discount,
        "charges": settings.charges,
        "withholding": settings.withholding,
        "comments": settings.comments,
        "settlement_enabled": str(settings.settlement).lower(),
        "print_policy": settings.print_policy,
        "document_date": invoice.document_date.strftime("%d/%m/%Y"),
        "document_number": invoice.document_number,
        "description": invoice.description,
        "net_value": _format_amount(invoice.net_value),
        "vat_value": _format_amount(invoice.vat_value),
        "total_value": _format_amount(invoice.total_value),
    }


def preview_workflow(
    workflow_path: str | Path,
    profile_name: str,
    item: PreparedInvoice,
) -> list[dict[str, str]]:
    profile = _profile(workflow_path, profile_name)
    context = build_invoice_context(item)
    preview: list[dict[str, str]] = []
    for step in profile["steps"]:
        if not _condition_matches(step, context):
            continue
        rendered = {"id": str(step.get("id", "")), "action": str(step["action"])}
        if "value" in step:
            value = _render(str(step["value"]), context)
            if step.get("skip_if_empty") and not value:
                continue
            rendered["value"] = "<secret>" if step.get("secret") else value
        preview.append(rendered)
    return preview


def execute_workflow(
    workflow_path: str | Path,
    profile_name: str,
    item: PreparedInvoice,
    *,
    allow_save: bool = False,
    artifacts_dir: str | Path = "pilot-data/failures",
) -> WorkflowExecution:
    context = build_invoice_context(item)
    return execute_profile(
        workflow_path,
        profile_name,
        context,
        allow_save=allow_save,
        artifacts_dir=artifacts_dir,
    )


def execute_profile(
    workflow_path: str | Path,
    profile_name: str,
    context: dict[str, str],
    *,
    allow_save: bool = False,
    artifacts_dir: str | Path = "pilot-data/failures",
    process_id: int | None = None,
) -> WorkflowExecution:
    desktop = _windows_desktop()
    workflow = _load_workflow(workflow_path)
    errors = validate_workflow_profile(workflow_path, profile_name)
    if errors:
        raise SoftOneAutomationError(f"Μη ολοκληρωμένο workflow: {', '.join(errors)}")

    profile = _profile(workflow_path, profile_name)
    missing = _missing_context(profile, context)
    if missing:
        raise SoftOneAutomationError(f"Λείπουν workflow values: {', '.join(missing)}")

    window = _find_window(
        desktop,
        profile.get("window", workflow["window"]),
        process_id=process_id,
    )
    executed: list[str] = []
    save_skipped = False
    saved = False
    step_id = "<start>"
    secret_step = False

    try:
        for step in profile["steps"]:
            if not _condition_matches(step, context):
                continue
            step_id = str(step.get("id", step["action"]))
            secret_step = bool(step.get("secret"))
            if step["action"] == "save" and not allow_save:
                save_skipped = True
                break
            if step.get("skip_if_empty") and "value" in step:
                if not _render(str(step["value"]), context):
                    continue
            try:
                if step["action"] == "switch_window":
                    window = _wait_window(
                        desktop,
                        step["selector"],
                        float(step.get("timeout_seconds", 10)),
                    )
                else:
                    _run_step(window, step, context)
            except SoftOneAutomationError:
                if step.get("optional"):
                    continue
                raise
            executed.append(step_id)
            if step["action"] == "save":
                saved = True
        return WorkflowExecution(
            profile=profile_name,
            executed_steps=tuple(executed),
            save_skipped=save_skipped,
            saved=saved,
        )
    except Exception as exc:
        screenshot = None
        if not secret_step:
            try:
                screenshot = _capture_failure(window, artifacts_dir, profile_name)
            except Exception:
                screenshot = None
        details = (
            "Αποτυχία εισαγωγής προστατευμένου πεδίου"
            if secret_step
            else str(exc)
        )
        raise SoftOneAutomationError(
            f"Αποτυχία στο βήμα {step_id}: {details}. Screenshot: {screenshot}"
        ) from exc


def launch_softone(
    workflow_path: str | Path,
    profile_name: str,
    executable_path: str | Path,
    arguments: tuple[str, ...] = (),
    *,
    timeout_seconds: int = 60,
) -> SoftOneLaunch:
    desktop = _windows_desktop()
    workflow = _load_workflow(workflow_path)
    profile = _profile(workflow_path, profile_name)
    selector = profile.get("window", workflow["window"])
    if _matching_windows(desktop, selector):
        return SoftOneLaunch(launched=False)

    executable = Path(executable_path)
    if not executable.is_file():
        raise SoftOneAutomationError(f"Δεν βρέθηκε το SoftOne: {executable}")
    if executable.suffix.lower() in {".lnk", ".url"}:
        process = subprocess.Popen(
            ["cmd.exe", "/c", "start", "", str(executable)],
            cwd=executable.parent,
        )
    else:
        process = subprocess.Popen(
            [str(executable), *arguments],
            cwd=executable.parent,
        )

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _matching_windows(desktop, selector) or _matching_process_windows(
            desktop,
            process.pid,
        ):
            return SoftOneLaunch(launched=True, process_id=process.pid)
        time.sleep(1)
    raise SoftOneAutomationError("Το SoftOne δεν έγινε έτοιμο στον διαθέσιμο χρόνο")


def _windows_desktop():
    if Desktop is None or keyboard is None:
        raise SoftOneAutomationError("Η SoftOne αυτοματοποίηση εκτελείται μόνο σε Windows")
    return Desktop(backend="uia")


def _load_workflow(workflow_path: str | Path) -> dict:
    try:
        workflow = json.loads(Path(workflow_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SoftOneAutomationError(f"Δεν διαβάστηκε το workflow: {exc}") from exc
    if not isinstance(workflow, dict):
        raise SoftOneAutomationError("Το workflow πρέπει να είναι JSON object")
    return workflow


def _profile(workflow_path: str | Path, profile_name: str) -> dict:
    workflow = _load_workflow(workflow_path)
    profiles = workflow.get("profiles", {})
    profile = profiles.get(profile_name) if isinstance(profiles, dict) else None
    if not isinstance(profile, dict):
        raise SoftOneAutomationError(f"Δεν υπάρχει workflow profile: {profile_name}")
    return profile


def _selector_has_identity(selector: dict) -> bool:
    direct_identity = any(
        selector.get(key)
        for key in ("auto_id", "auto_id_re", "class_name", "class_name_re", "title", "title_re")
    ) or isinstance(selector.get("anchor"), dict)
    descendant = selector.get("descendant")
    descendant_identity = isinstance(descendant, dict) and _selector_has_identity(
        descendant
    )
    alternatives = selector.get("any_of")
    alternative_identity = isinstance(alternatives, list) and any(
        isinstance(alternative, dict) and _selector_has_identity(alternative)
        for alternative in alternatives
    )
    return direct_identity or descendant_identity or alternative_identity


def _find_window(desktop, selector: dict, *, process_id: int | None = None):
    matches = _matching_windows(desktop, selector)
    if not matches and process_id is not None:
        matches = _matching_process_windows(desktop, process_id)
    if not matches:
        raise SoftOneAutomationError("Δεν βρέθηκε το ενεργό παράθυρο SoftOne")
    matches.sort(key=_area, reverse=True)
    return matches[0]


def _matching_windows(desktop, selector: dict) -> list:
    return [
        window for window in desktop.windows() if _window_matches(window, selector)
    ]


def _window_matches(window, selector: dict) -> bool:
    alternatives = selector.get("any_of")
    if isinstance(alternatives, list):
        return any(
            isinstance(alternative, dict) and _window_matches(window, alternative)
            for alternative in alternatives
        )
    if not _matches(window, selector):
        return False
    descendant = selector.get("descendant")
    if not isinstance(descendant, dict):
        return True
    try:
        return any(_matches(control, descendant) for control in window.descendants())
    except Exception:
        return False


def _matching_process_windows(desktop, process_id: int) -> list:
    return [
        window
        for window in desktop.windows()
        if window.element_info.process_id == process_id
    ]


def _wait_window(desktop, selector: dict, timeout: float):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        matches = _matching_windows(desktop, selector)
        if matches:
            matches.sort(key=_area, reverse=True)
            return matches[0]
        time.sleep(0.1)
    raise SoftOneAutomationError(f"Δεν βρέθηκε παράθυρο: {_selector_label(selector)}")


def _find_control(window, selector: dict, timeout: float = 10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        controls = [control for control in window.descendants() if _matches(control, selector)]
        if isinstance(selector.get("anchor"), dict):
            controls = _rank_near_anchor(window, controls, selector["anchor"])
        if controls:
            index = int(selector.get("found_index", 0))
            if index < len(controls):
                return controls[index]
        time.sleep(0.1)
    raise SoftOneAutomationError(f"Δεν βρέθηκε control: {_selector_label(selector)}")


def _matches(control, selector: dict) -> bool:
    info = control.element_info
    values = {
        "auto_id": str(info.automation_id or ""),
        "class_name": str(info.class_name or ""),
        "control_type": str(info.control_type or ""),
        "title": str(info.name or ""),
    }
    for key in ("auto_id", "class_name", "control_type", "title"):
        if selector.get(key) and values[key] != str(selector[key]):
            return False
    for key in ("auto_id", "class_name", "title"):
        pattern = selector.get(f"{key}_re")
        if pattern and re.search(str(pattern), values[key], re.IGNORECASE) is None:
            return False
    return True


def _rank_near_anchor(window, controls: list, anchor_config: dict) -> list:
    anchor_selector = anchor_config.get("selector")
    if not isinstance(anchor_selector, dict):
        return []
    anchors = [control for control in window.descendants() if _matches(control, anchor_selector)]
    if not anchors:
        return []
    anchor = anchors[int(anchor_config.get("found_index", 0))]
    anchor_rect = anchor.rectangle()
    direction = anchor_config.get("direction", "right")
    max_distance = float(anchor_config.get("max_distance", 800))
    ranked = []
    for control in controls:
        rectangle = control.rectangle()
        if direction == "right":
            primary = rectangle.left - anchor_rect.right
            secondary = abs(_center_y(rectangle) - _center_y(anchor_rect))
        elif direction == "below":
            primary = rectangle.top - anchor_rect.bottom
            secondary = abs(_center_x(rectangle) - _center_x(anchor_rect))
        else:
            return []
        if -5 <= primary <= max_distance:
            ranked.append((primary + secondary * 2, control))
    ranked.sort(key=lambda item: item[0])
    return [control for _, control in ranked]


def _run_step(window, step: dict, context: dict[str, str]) -> None:
    action = step["action"]
    timeout = float(step.get("timeout_seconds", 10))
    if action in {"assert", "wait_present"}:
        _find_control(window, step["selector"], timeout)
        return
    if action in {"assert_absent", "wait_absent"}:
        _wait_absent(window, step["selector"], timeout)
        return
    if action == "press_keys":
        keyboard.send_keys(
            str(step["keys"]),
            with_spaces=True,
            vk_packet=True,
        )
        return
    if action in {"click", "save"}:
        _find_control(window, step["selector"], timeout).click_input()
        return
    value = _render(str(step["value"]), context)
    if action == "type_focused":
        _type_focused(window, value, step)
        return
    if action == "set":
        _set_control(_find_control(window, step["selector"], timeout), value, step)
        return
    if action == "grid_set":
        _set_grid_cell(window, step, value, timeout)
        return
    raise SoftOneAutomationError(f"Άγνωστο action: {action}")


def _set_control(control, value: str, step: dict) -> None:
    try:
        control.set_edit_text(value)
    except Exception:
        control.click_input()
        keyboard.send_keys("^a{BACKSPACE}")
        keyboard.send_keys(_escape_keys(value), with_spaces=True, vk_packet=True)
    if step.get("submit_keys"):
        keyboard.send_keys(str(step["submit_keys"]), with_spaces=True, vk_packet=True)


def _type_focused(window, value: str, step: dict) -> None:
    window.set_focus()
    keyboard.send_keys("^a{BACKSPACE}")
    keyboard.send_keys(_escape_keys(value), with_spaces=True, vk_packet=True)
    if step.get("submit_keys"):
        keyboard.send_keys(str(step["submit_keys"]), with_spaces=True, vk_packet=True)


def _escape_keys(value: str) -> str:
    special = {
        "+": "{+}",
        "^": "{^}",
        "%": "{%}",
        "~": "{~}",
        "(": "{(}",
        ")": "{)}",
        "{": "{{}",
        "}": "{}}",
    }
    return "".join(special.get(character, character) for character in value)


def _set_grid_cell(window, step: dict, value: str, timeout: float) -> None:
    grid = _find_control(window, step["grid"], timeout)
    column = _find_control(window, step["column"], timeout)
    grid_rect = grid.rectangle()
    column_rect = column.rectangle()
    row_height = int(step.get("row_height", max(column_rect.height(), 24)))
    row_index = int(step.get("row_index", 0))
    x = _center_x(column_rect)
    y = min(grid_rect.bottom - 4, column_rect.bottom + row_height // 2 + row_index * row_height)
    grid.click_input(coords=(x - grid_rect.left, y - grid_rect.top))
    keyboard.send_keys("^a{BACKSPACE}")
    keyboard.send_keys(_escape_keys(value), with_spaces=True, vk_packet=True)
    if step.get("submit_keys"):
        keyboard.send_keys(str(step["submit_keys"]), with_spaces=True, vk_packet=True)


def _wait_absent(window, selector: dict, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(_matches(control, selector) for control in window.descendants()):
            return
        time.sleep(0.1)
    raise SoftOneAutomationError(f"Το control παρέμεινε ορατό: {_selector_label(selector)}")


def _missing_context(profile: dict, context: dict[str, str]) -> list[str]:
    required = profile.get("required_context", [])
    return [str(key) for key in required if not context.get(str(key))]


def _condition_matches(step: dict, context: dict[str, str]) -> bool:
    condition = step.get("when")
    if condition is None:
        return True
    if not isinstance(condition, dict):
        raise SoftOneAutomationError("Το when πρέπει να είναι JSON object")
    return all(context.get(str(key)) == str(value) for key, value in condition.items())


def _render(template: str, context: dict[str, str]) -> str:
    fields = [field for _, field, _, _ in Formatter().parse(template) if field]
    missing = [field for field in fields if field not in context]
    if missing:
        raise SoftOneAutomationError(f"Άγνωστα placeholders: {', '.join(missing)}")
    return template.format_map(context)


def _format_amount(value: Decimal) -> str:
    return f"{value:.2f}".replace(".", ",")


def _capture_failure(window, artifacts_dir: str | Path, profile_name: str) -> Path:
    directory = Path(artifacts_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = directory / f"{profile_name}-{timestamp}.png"
    window.capture_as_image().save(path)
    return path


def _selector_label(selector: dict) -> str:
    if isinstance(selector.get("descendant"), dict):
        return f"descendant({_selector_label(selector['descendant'])})"
    if isinstance(selector.get("any_of"), list):
        return "any_of"
    for key in ("title", "title_re", "auto_id", "auto_id_re", "class_name"):
        if selector.get(key):
            return f"{key}={selector[key]}"
    return "<relative selector>"


def _area(control) -> int:
    rectangle = control.rectangle()
    return max(0, rectangle.width()) * max(0, rectangle.height())


def _center_x(rectangle) -> int:
    return rectangle.left + rectangle.width() // 2


def _center_y(rectangle) -> int:
    return rectangle.top + rectangle.height() // 2
