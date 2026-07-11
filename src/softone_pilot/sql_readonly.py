from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from softone_pilot.config import SqlSettings
from softone_pilot.models import DuplicateRecord, SqlSupplier

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

    def _connection(self):
        if self.connection is None:
            raise SqlReadOnlyError("Η read-only SQL σύνδεση δεν είναι ανοικτή")
        return self.connection
