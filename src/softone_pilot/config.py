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
class AutomationSettings:
    enabled: bool
    executable_path: str
    arguments: tuple[str, ...]
    inbox_path: str
    processed_path: str
    failed_path: str
    startup_timeout_seconds: int
    credential_target: str
    startup_profile: str
    navigation_profile: str


@dataclass(frozen=True)
class AppConfig:
    sql: SqlSettings
    automation: AutomationSettings
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
    automation_raw = raw.get("automation", {})
    automation = AutomationSettings(
        enabled=bool(automation_raw.get("enabled", False)),
        executable_path=str(automation_raw.get("executable_path", "")),
        arguments=tuple(str(item) for item in automation_raw.get("arguments", [])),
        inbox_path=str(automation_raw.get("inbox_path", "inbox")),
        processed_path=str(automation_raw.get("processed_path", "processed")),
        failed_path=str(automation_raw.get("failed_path", "failed")),
        startup_timeout_seconds=int(automation_raw.get("startup_timeout_seconds", 60)),
        credential_target=str(
            automation_raw.get("credential_target", "SoftOne PDF Pilot")
        ),
        startup_profile=str(automation_raw.get("startup_profile", "softone.login")),
        navigation_profile=str(
            automation_raw.get(
                "navigation_profile",
                "creditor_expense.open_create",
            )
        ),
    )
    suppliers = {
        vat: SupplierSettings(
            name=str(item.get("name", "")),
            series_code=str(item.get("series_code", "")),
            line_code=str(item.get("line_code", "")),
            payment_method=str(item.get("payment_method", "")),
            settlement=bool(item.get("settlement", False)),
            workflow_profile=str(
                item.get("workflow_profile", "creditor_expense.create")
            ),
            company_branch=str(item.get("company_branch", "")),
            supplier_branch=str(item.get("supplier_branch", "")),
            warehouse=str(item.get("warehouse", "")),
            document_type=str(item.get("document_type", "")),
            vat_regime=str(item.get("vat_regime", "")),
            quantity=str(item.get("quantity", "1")),
            discount=str(item.get("discount", "")),
            charges=str(item.get("charges", "")),
            withholding=str(item.get("withholding", "")),
            comments=str(item.get("comments", "")),
            print_policy=str(item.get("print_policy", "none")),
        )
        for vat, item in raw.get("suppliers", {}).items()
    }
    return AppConfig(sql=sql, automation=automation, suppliers=suppliers)


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
        automation=AutomationSettings(
            enabled=False,
            executable_path="",
            arguments=(),
            inbox_path="inbox",
            processed_path="processed",
            failed_path="failed",
            startup_timeout_seconds=60,
            credential_target="SoftOne PDF Pilot",
            startup_profile="softone.login",
            navigation_profile="creditor_expense.open_create",
        ),
        suppliers={},
    )
