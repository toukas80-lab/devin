"""Read-only export of company 3000 profit inputs (sales, cost, purchases, ledger) to CSV."""

import csv
import os
import sys
from pathlib import Path

import pyodbc

PERIODS = (
    "(VALUES ('2025YTD','2025-01-01','2025-10-24'),"
    "('2026YTD','2026-01-01','2026-10-24'),"
    "('2025FULL','2025-01-01','2026-01-01')) per(P,D1,D2)"
)
SALES_TYPES = "(102,103,131,151,152,181)"
SIGN = "CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END"

QUERIES = {
    "sales_items": [
        f"""
SELECT per.P, m.CODE, m.NAME, m.SODTYPE,
       CAST(SUM(l.QTY1 * {SIGN}) AS decimal(18,3)) AS QTY,
       CAST(SUM(l.LINEVAL * {SIGN}) AS decimal(18,2)) AS NETVAL
FROM dbo.MTRLINES l
JOIN dbo.FINDOC f ON f.FINDOC = l.FINDOC
JOIN dbo.FPRMS p ON p.FPRMS = f.FPRMS AND p.COMPANY = f.COMPANY AND p.SOSOURCE = f.SOSOURCE
JOIN dbo.MTRL m ON m.MTRL = l.MTRL AND m.COMPANY = f.COMPANY
JOIN {PERIODS} ON f.TRNDATE >= per.D1 AND f.TRNDATE < per.D2
WHERE f.COMPANY = 3000 AND f.SOSOURCE = 1351 AND f.ISCANCEL = 0 AND p.TFPRMS IN {SALES_TYPES}
GROUP BY per.P, m.CODE, m.NAME, m.SODTYPE
ORDER BY per.P, m.CODE"""
    ],
    "docs_overview": [
        """
SELECT per.P, f.SOSOURCE, p.NAME AS FPRMS_NAME, p.TFPRMS, COUNT(*) AS DOCS,
       CAST(SUM(f.NETAMNT) AS decimal(18,2)) AS NETAMNT,
       CAST(SUM(f.VATAMNT) AS decimal(18,2)) AS VATAMNT,
       CAST(SUM(f.SUMAMNT) AS decimal(18,2)) AS SUMAMNT
FROM dbo.FINDOC f
JOIN dbo.FPRMS p ON p.FPRMS = f.FPRMS AND p.COMPANY = f.COMPANY AND p.SOSOURCE = f.SOSOURCE
JOIN """
        + PERIODS
        + """ ON f.TRNDATE >= per.D1 AND f.TRNDATE < per.D2
WHERE f.COMPANY = 3000 AND f.ISCANCEL = 0
GROUP BY per.P, f.SOSOURCE, p.NAME, p.TFPRMS
ORDER BY per.P, f.SOSOURCE, p.TFPRMS"""
    ],
    "purchase_lines": [
        """
SELECT per.P, p.NAME AS FPRMS_NAME, p.TFPRMS, m.SODTYPE,
       COUNT(DISTINCT f.FINDOC) AS DOCS,
       CAST(SUM(l.QTY1) AS decimal(18,3)) AS QTY,
       CAST(SUM(l.LINEVAL) AS decimal(18,2)) AS NETVAL
FROM dbo.MTRLINES l
JOIN dbo.FINDOC f ON f.FINDOC = l.FINDOC
JOIN dbo.FPRMS p ON p.FPRMS = f.FPRMS AND p.COMPANY = f.COMPANY AND p.SOSOURCE = f.SOSOURCE
JOIN dbo.MTRL m ON m.MTRL = l.MTRL AND m.COMPANY = f.COMPANY
JOIN """
        + PERIODS
        + """ ON f.TRNDATE >= per.D1 AND f.TRNDATE < per.D2
WHERE f.COMPANY = 3000 AND f.SOSOURCE = 1251 AND f.ISCANCEL = 0
GROUP BY per.P, p.NAME, p.TFPRMS, m.SODTYPE
ORDER BY per.P, p.TFPRMS, m.SODTYPE"""
    ],
    "purchase_items": [
        """
SELECT YEAR(f.TRNDATE) AS YR, p.TFPRMS, m.CODE,
       CAST(SUM(l.QTY1) AS decimal(18,3)) AS QTY,
       CAST(SUM(l.LINEVAL) AS decimal(18,2)) AS NETVAL
FROM dbo.MTRLINES l
JOIN dbo.FINDOC f ON f.FINDOC = l.FINDOC
JOIN dbo.FPRMS p ON p.FPRMS = f.FPRMS AND p.COMPANY = f.COMPANY AND p.SOSOURCE = f.SOSOURCE
JOIN dbo.MTRL m ON m.MTRL = l.MTRL AND m.COMPANY = f.COMPANY
WHERE f.COMPANY = 3000 AND f.SOSOURCE = 1251 AND f.ISCANCEL = 0 AND m.SODTYPE = 51
  AND f.TRNDATE >= '2018-01-01' AND f.TRNDATE < '2026-10-24'
GROUP BY YEAR(f.TRNDATE), p.TFPRMS, m.CODE
ORDER BY 1, 2, 3"""
    ],
    "item_findata": [
        """
SELECT m.CODE, d.FISCPRD,
       CAST(SUM(d.IMPQTY1) AS decimal(18,3)) AS IMPQTY1, CAST(SUM(d.IMPVAL) AS decimal(18,2)) AS IMPVAL,
       CAST(SUM(d.SALQTY1) AS decimal(18,3)) AS SALQTY1, CAST(SUM(d.SALVAL) AS decimal(18,2)) AS SALVAL
FROM dbo.MTRLFINDATA d
JOIN dbo.MTRL m ON m.MTRL = d.MTRL AND m.COMPANY = d.COMPANY
WHERE d.COMPANY = 3000 AND d.FISCPRD BETWEEN 2018 AND 2026
GROUP BY m.CODE, d.FISCPRD
ORDER BY m.CODE, d.FISCPRD""",
        """
SELECT m.CODE, d.FISCPRD,
       CAST(SUM(d.IMPQTY1) AS decimal(18,3)) AS IMPQTY1, CAST(SUM(d.IMPVAL) AS decimal(18,2)) AS IMPVAL,
       CAST(SUM(d.SALQTY1) AS decimal(18,3)) AS SALQTY1, CAST(SUM(d.SALVAL) AS decimal(18,2)) AS SALVAL
FROM dbo.MTRLFINDATA d
JOIN dbo.MTRL m ON m.MTRL = d.MTRL
WHERE m.COMPANY = 3000 AND d.FISCPRD BETWEEN 2018 AND 2026
GROUP BY m.CODE, d.FISCPRD
ORDER BY m.CODE, d.FISCPRD""",
    ],
    "ledger_6x_7x": [
        """
SELECT d.FISCPRD, d.PERIOD, LEFT(a.CODE, 2) AS ACN2,
       CAST(SUM(d.DEBIT) AS decimal(18,2)) AS DEBIT, CAST(SUM(d.CREDIT) AS decimal(18,2)) AS CREDIT
FROM dbo.ACNFINDATA d
JOIN dbo.ACN a ON a.ACN = d.ACN AND a.COMPANY = d.COMPANY
WHERE d.COMPANY = 3000 AND d.FISCPRD IN (2025, 2026)
  AND (a.CODE LIKE '6%' OR a.CODE LIKE '7%' OR a.CODE LIKE '2%')
GROUP BY d.FISCPRD, d.PERIOD, LEFT(a.CODE, 2)
ORDER BY 1, 2, 3""",
        """
SELECT d.FISCPRD, d.PERIOD, LEFT(a.CODE, 2) AS ACN2,
       CAST(SUM(d.DEBIT) AS decimal(18,2)) AS DEBIT, CAST(SUM(d.CREDIT) AS decimal(18,2)) AS CREDIT
FROM dbo.ACNFINDATA d
JOIN dbo.ACN a ON a.ACN = d.ACN
WHERE a.COMPANY = 3000 AND d.FISCPRD IN (2025, 2026)
  AND (a.CODE LIKE '6%' OR a.CODE LIKE '7%' OR a.CODE LIKE '2%')
GROUP BY d.FISCPRD, d.PERIOD, LEFT(a.CODE, 2)
ORDER BY 1, 2, 3""",
    ],
}


def connect() -> pyodbc.Connection:
    password = os.environ["SQLCMDPASSWORD"]
    errors = []
    for driver in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        try:
            return pyodbc.connect(
                f"DRIVER={{{driver}}};SERVER=.\\SOFTONE;DATABASE=FOUNTOUKAS;"
                f"UID=devin_ro;PWD={password};TrustServerCertificate=yes;",
                timeout=30,
                autocommit=False,
            )
        except pyodbc.Error as exc:
            errors.append(f"{driver}: {exc}")
    raise SystemExit("Αποτυχία σύνδεσης:\n" + "\n".join(errors))


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data/profit")
    out_dir.mkdir(parents=True, exist_ok=True)
    log = []
    conn = connect()
    try:
        for name, variants in QUERIES.items():
            for index, sql in enumerate(variants, start=1):
                try:
                    cursor = conn.execute(sql)
                    rows = cursor.fetchall()
                    header = [col[0] for col in cursor.description]
                except pyodbc.Error as exc:
                    log.append(f"{name} v{index}: ΣΦΑΛΜΑ {exc}")
                    conn.rollback()
                    continue
                with open(out_dir / f"{name}.csv", "w", encoding="utf-8-sig", newline="") as fh:
                    writer = csv.writer(fh, delimiter=";")
                    writer.writerow(header)
                    writer.writerows(["" if v is None else v for v in row] for row in rows)
                log.append(f"{name} v{index}: OK {len(rows)} γραμμές")
                break
    finally:
        conn.rollback()
        conn.close()
    (out_dir / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
