from __future__ import annotations

import json
import platform
from pathlib import Path


class SoftOneAutomationError(RuntimeError):
    pass


def inspect_softone_controls(workflow_path: str | Path, output_path: str | Path) -> Path:
    if platform.system() != "Windows":
        raise SoftOneAutomationError("Η καταγραφή SoftOne controls εκτελείται μόνο σε Windows")

    try:
        from pywinauto import Desktop
    except ImportError as exc:
        raise SoftOneAutomationError("Δεν είναι εγκατεστημένο το pywinauto") from exc

    workflow = json.loads(Path(workflow_path).read_text(encoding="utf-8"))
    title_re = workflow.get("window", {}).get("title_re", ".*SoftOne.*")
    window = Desktop(backend="uia").window(title_re=title_re)
    window.wait("exists enabled visible ready", timeout=15)

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


def validate_workflow_profile(workflow_path: str | Path) -> list[str]:
    workflow = json.loads(Path(workflow_path).read_text(encoding="utf-8"))
    missing = []
    for name, selector in workflow.get("controls", {}).items():
        if not selector.get("title") and not selector.get("auto_id"):
            missing.append(name)
    return missing


def commit_is_available(workflow_path: str | Path) -> bool:
    return not validate_workflow_profile(workflow_path)
