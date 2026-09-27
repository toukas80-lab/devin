from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from softone_pilot.config import SqlSettings
from softone_pilot.models import DuplicateRecord, SqlSupplier
from softone_pilot.valuation import BalanceSnapshot, YearFigures

if TYPE_CHECKING:
    import pyodbc


class SqlReadOnlyError(RuntimeError):
    pass


class SoftOneReadOnlyRepository(AbstractContextManager):
    def __init__(self, settings: SqlSettings) -> None:
        self.settings = settings
        self.connection: pyodbc.Connection | None = None

    def __enter__(self) -> SoftOneReadOnlyRepository:
        if not self.settings.trusted_connection:
            raise SqlReadOnlyError("Το pilot υποστηρίζει μόνο Windows trusted connection")
        try:
            import pyodbc
        except ImportError as exc:
            raise SqlReadOnlyError("Το pyodbc είναι διαθέσιμο μόνο στο Windows build") from exc

        connection_string = (
            f"DRIVER={{{self.settings.driver}}};"
            f"SERVER={self.settings.server};"
            f"DATABASE={self.settings.database};"
            "Trusted_Connection=yes;"
            "ApplicationIntent=ReadOnly;"
            "TrustServerCertificate=yes;"
        )
        try:
            self.connection = pyodbc.connect(
                connection_string,
                timeout=self.settings.timeout_seconds,
                autocommit=False,
            )
            self.connection.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
        except pyodbc.Error as exc:
            raise SqlReadOnlyError(f"Αποτυχία read-only σύνδεσης SQL: {exc}") from exc
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.connection is not None:
            self.connection.rollback()
            self.connection.close()
            self.connection = None

    def find_supplier(self, vat: str) -> SqlSupplier | None:
        cursor = self._connection().execute(
            """
            SELECT TOP (1)
                TRDR,
                LTRIM(RTRIM(CODE)),
                LTRIM(RTRIM(NAME)),
                LTRIM(RTRIM(AFM)),
                COALESCE(CONVERT(varchar(30), PAYMENT), '')
            FROM dbo.TRDR
            WHERE REPLACE(REPLACE(UPPER(LTRIM(RTRIM(AFM))), 'EL', ''), ' ', '') = ?
              AND ISACTIVE = 1
            ORDER BY TRDR
            """,
            vat,
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return SqlSupplier(
            trdr_id=int(row[0]),
            code=str(row[1] or ""),
            name=str(row[2] or ""),
            vat=str(row[3] or ""),
            payment=str(row[4] or ""),
        )

    def find_duplicate(
        self,
        vat: str,
        document_number: str,
        document_date: date,
    ) -> DuplicateRecord | None:
        plain_number = document_number.rsplit("-", 1)[-1]
        cursor = self._connection().execute(
            """
            SELECT TOP (1)
                f.FINDOC,
                CONVERT(date, f.TRNDATE),
                LTRIM(RTRIM(COALESCE(f.FINCODE, ''))),
                CONVERT(varchar(50), COALESCE(f.SERIESNUM, 0)),
                COALESCE(f.SUMAMNT, 0)
            FROM dbo.FINDOC AS f
            INNER JOIN dbo.TRDR AS t ON t.TRDR = f.TRDR
            WHERE REPLACE(REPLACE(UPPER(LTRIM(RTRIM(t.AFM))), 'EL', ''), ' ', '') = ?
              AND CONVERT(date, f.TRNDATE) = ?
              AND (
                    LTRIM(RTRIM(COALESCE(f.FINCODE, ''))) = ?
                 OR LTRIM(RTRIM(COALESCE(f.FINCODE, ''))) LIKE ?
                 OR CONVERT(varchar(50), COALESCE(f.SERIESNUM, 0)) = ?
              )
            ORDER BY f.FINDOC DESC
            """,
            vat,
            document_date,
            document_number,
            f"%{document_number}%",
            plain_number,
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return DuplicateRecord(
            findoc_id=int(row[0]),
            document_date=row[1],
            fincode=str(row[2] or ""),
            series_number=str(row[3] or ""),
            total=Decimal(str(row[4])).quantize(Decimal("0.01")),
        )

    def fiscal_years(self, count: int, include_current: bool = False) -> list[int]:
        cursor = self._connection().execute(
            """
            SELECT DISTINCT TOP (?) FISCPRD FROM dbo.MTRLFINDATA
            WHERE ? = 1 OR FISCPRD < YEAR(GETDATE())
            ORDER BY FISCPRD DESC
            """,
            count,
            1 if include_current else 0,
        )
        return sorted(int(row[0]) for row in cursor.fetchall())

    def yearly_figures(self, years: list[int]) -> list[YearFigures]:
        if not years:
            return []
        placeholders = ",".join("?" for _ in years)
        trading = (
            self._connection()
            .execute(
                f"""
            SELECT y.FISCPRD,
                   COALESCE(SUM(y.SALVAL), 0),
                   COALESCE(SUM(CASE WHEN c.IMPQTY > 0
                                     THEN y.SALQTY1 * c.IMPVAL / c.IMPQTY ELSE 0 END), 0)
            FROM dbo.MTRLFINDATA AS y
            OUTER APPLY (
                SELECT SUM(h.IMPVAL) AS IMPVAL, SUM(h.IMPQTY1) AS IMPQTY
                FROM dbo.MTRLFINDATA AS h
                WHERE h.MTRL = y.MTRL AND h.FISCPRD <= y.FISCPRD
            ) AS c
            WHERE y.FISCPRD IN ({placeholders})
            GROUP BY y.FISCPRD
            """,
                *years,
            )
            .fetchall()
        )
        expenses = {
            int(row[0]): Decimal(str(row[1]))
            for row in self._connection()
            .execute(
                f"""
                SELECT d.FISCPRD, COALESCE(SUM(d.DEBIT - d.CREDIT), 0)
                FROM dbo.ACNFINDATA AS d
                INNER JOIN dbo.ACN AS a ON a.ACN = d.ACN
                WHERE d.FISCPRD IN ({placeholders}) AND a.CODE LIKE '6%'
                GROUP BY d.FISCPRD
                HAVING SUM(ABS(d.DEBIT) + ABS(d.CREDIT)) > 0
                """,
                *years,
            )
            .fetchall()
        }
        return [
            YearFigures(
                fiscal_year=int(row[0]),
                revenue=Decimal(str(row[1])),
                cost_of_goods=Decimal(str(row[2])),
                operating_expenses=expenses.get(int(row[0])),
            )
            for row in trading
        ]

    def balance_snapshot(self, fiscal_year: int) -> BalanceSnapshot:
        connection = self._connection()

        def scope(table: str, alias: str) -> str:
            has_opening = connection.execute(
                f"SELECT COUNT(*) FROM dbo.{table} WHERE FISCPRD = ? AND PERIOD = 0",
                fiscal_year,
            ).fetchone()[0]
            operator = "=" if has_opening else "<="
            return f"{alias}.FISCPRD {operator} ?"

        inventory = connection.execute(
            f"""
            SELECT COALESCE(SUM(m.IMPVAL - m.EXPVAL), 0) FROM dbo.MTRLFINDATA AS m
            WHERE {scope("MTRLFINDATA", "m")}
            """,
            fiscal_year,
        ).fetchone()[0]
        trader_scope = scope("TRDFINDATA", "d")
        receivables = connection.execute(
            f"""
            SELECT COALESCE(SUM(d.DEBIT - d.CREDIT), 0)
            FROM dbo.TRDFINDATA AS d INNER JOIN dbo.TRDR AS t ON t.TRDR = d.TRDR
            WHERE {trader_scope} AND t.SODTYPE = 13
            """,
            fiscal_year,
        ).fetchone()[0]
        payables = connection.execute(
            f"""
            SELECT COALESCE(SUM(d.CREDIT - d.DEBIT), 0)
            FROM dbo.TRDFINDATA AS d INNER JOIN dbo.TRDR AS t ON t.TRDR = d.TRDR
            WHERE {trader_scope} AND t.SODTYPE = 12
            """,
            fiscal_year,
        ).fetchone()[0]
        cash = connection.execute(
            f"""
            SELECT COALESCE(SUM(d.DEBIT - d.CREDIT), 0)
            FROM dbo.ACNFINDATA AS d INNER JOIN dbo.ACN AS a ON a.ACN = d.ACN
            WHERE {scope("ACNFINDATA", "d")} AND a.CODE LIKE '38%'
            """,
            fiscal_year,
        ).fetchone()[0]
        return BalanceSnapshot(
            inventory_value=Decimal(str(inventory)),
            receivables=Decimal(str(receivables)),
            payables=Decimal(str(payables)),
            cash=Decimal(str(cash)),
        )

    def _connection(self):
        if self.connection is None:
            raise SqlReadOnlyError("Η read-only SQL σύνδεση δεν είναι ανοικτή")
        return self.connection
