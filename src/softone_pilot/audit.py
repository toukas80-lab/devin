from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from softone_pilot.models import PreparedInvoice


def write_dry_run_audit(
    path: str | Path,
    items: list[PreparedInvoice],
    parse_errors: list[str],
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": "dry_run",
        "summary": {
            "total": len(items),
            "ready": sum(item.ready for item in items),
            "blocked": sum(not item.ready for item in items),
            "parse_errors": len(parse_errors),
        },
        "items": [
            {
                "source_file": item.invoice.source_path.name,
                "supplier_vat": item.invoice.supplier_vat,
                "document_number": item.invoice.document_number,
                "document_date": item.invoice.document_date.isoformat(),
                "total": format(item.invoice.total_value, ".2f"),
                "ready": item.ready,
                "errors": list(item.errors),
                "warnings": list(item.warnings),
            }
            for item in items
        ],
        "parse_errors": parse_errors,
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
    return target
