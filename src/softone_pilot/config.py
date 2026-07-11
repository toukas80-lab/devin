from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from softone_pilot.models import SupplierSettings


@dataclass(frozen=True)
class SqlSettings:
    enabled: bool
    server: str
    database: str
    driver: str
    trusted_connection: bool
    timeout_seconds: int


@dataclass(frozen=True)
class AppConfig:
    sql: SqlSettings
    suppliers: dict[str, SupplierSettings]


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    sql_raw = raw.get("sql", {})
    sql = SqlSettings(
        enabled=bool(sql_raw.get("enabled", True)),
        server=str(sql_raw.get("server", r".\SOFTONE")),
        database=str(sql_raw.get("database", "FOUNTOUKAS")),
        driver=str(sql_raw.get("driver", "ODBC Driver 17 for SQL Server")),
        trusted_connection=bool(sql_raw.get("trusted_connection", True)),
        timeout_seconds=int(sql_raw.get("timeout_seconds", 10)),
    )
    suppliers = {
        vat: SupplierSettings(
            name=str(item.get("name", "")),
            series_code=str(item.get("series_code", "")),
            line_code=str(item.get("line_code", "")),
            payment_method=str(item.get("payment_method", "")),
            settlement=bool(item.get("settlement", False)),
        )
        for vat, item in raw.get("suppliers", {}).items()
    }
    return AppConfig(sql=sql, suppliers=suppliers)


def default_config() -> AppConfig:
    return AppConfig(
        sql=SqlSettings(
            enabled=False,
            server=r".\SOFTONE",
            database="FOUNTOUKAS",
            driver="ODBC Driver 17 for SQL Server",
            trusted_connection=True,
            timeout_seconds=10,
        ),
        suppliers={},
    )
