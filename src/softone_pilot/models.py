from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class InvoiceLine:
    code: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_pct: Decimal
    value: Decimal
    vat_pct: Decimal
    category: str = ""


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
    vat_pct: Decimal = Decimal("24")
    lines: tuple[InvoiceLine, ...] = ()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["source_path"] = str(self.source_path)
        data["document_date"] = self.document_date.isoformat()
        for key in ("net_value", "vat_value", "total_value", "vat_pct"):
            data[key] = format(data[key], ".2f")
        data["lines"] = [
            {k: (format(v, ".2f") if isinstance(v, Decimal) else v) for k, v in line.items()}
            for line in data["lines"]
        ]
        data.pop("raw_text", None)
        return data


@dataclass(frozen=True)
class SupplierSettings:
    name: str
    series_code: str
    line_code: str
    payment_method: str
    settlement: bool
    kind: str = "expense"
    trdr_code: str = ""
    item_map: dict[str, str] = field(default_factory=dict)
    line_codes: dict[str, str] = field(default_factory=dict)

    @property
    def has_expense_account(self) -> bool:
        return bool(self.line_code or self.line_codes)

    @property
    def is_complete(self) -> bool:
        if self.kind == "purchase":
            return all((self.series_code, self.payment_method)) and bool(self.item_map)
        return all((self.series_code, self.payment_method)) and self.has_expense_account

    def expense_account(self, line: InvoiceLine) -> str:
        if line.category:
            account = self.line_codes.get(line.category)
            if not account:
                raise ValueError(
                    f"χωρίς λογαριασμό δαπάνης (line_codes) για κατηγορία {line.category}"
                )
            return account
        if not self.line_code:
            raise ValueError("λείπει line_code (λογαριασμός δαπάνης)")
        return self.line_code


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
