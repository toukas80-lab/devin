from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class InvoiceData:
    source_path: Path
    supplier_name: str
    supplier_vat: str
    document_number: str
    document_date: date
    net_value: Decimal
    vat_value: Decimal
    total_value: Decimal
    description: str
    raw_text: str = field(repr=False)

    def to_dict(self) -> dict[str, str]:
        data = asdict(self)
        data["source_path"] = str(self.source_path)
        data["document_date"] = self.document_date.isoformat()
        for key in ("net_value", "vat_value", "total_value"):
            data[key] = format(data[key], ".2f")
        data.pop("raw_text", None)
        return data


@dataclass(frozen=True)
class SupplierSettings:
    name: str
    series_code: str
    line_code: str
    payment_method: str
    settlement: bool

    @property
    def is_complete(self) -> bool:
        return all((self.series_code, self.line_code, self.payment_method))


@dataclass(frozen=True)
class SqlSupplier:
    trdr_id: int
    code: str
    name: str
    vat: str
    payment: str


@dataclass(frozen=True)
class DuplicateRecord:
    findoc_id: int
    document_date: date
    fincode: str
    series_number: str
    total: Decimal


@dataclass(frozen=True)
class PreparedInvoice:
    invoice: InvoiceData
    settings: SupplierSettings | None
    sql_supplier: SqlSupplier | None
    duplicate: DuplicateRecord | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "invoice": self.invoice.to_dict(),
            "settings": asdict(self.settings) if self.settings else None,
            "sql_supplier": asdict(self.sql_supplier) if self.sql_supplier else None,
            "duplicate": asdict(self.duplicate) if self.duplicate else None,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "ready": self.ready,
        }
