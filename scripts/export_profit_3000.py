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


NON_INVOICE_TYPES = {101, 104, 105, 154, 201, 202}
LABELS = {"2025YTD": "2025 (1/1-23/10)", "2026YTD": "2026 (1/1-23/10)", "2025FULL": "2025 (όλο)"}


def num(value) -> float:
    return float(value or 0)


def summarize(data: dict) -> str:
    def rows(name):
        header, body = data.get(name, ([], []))
        return [dict(zip(header, r, strict=False)) for r in body]

    findata = {}
    for r in rows("item_findata"):
        findata.setdefault(r["CODE"], []).append(
            (int(r["FISCPRD"]), num(r["IMPQTY1"]), num(r["IMPVAL"]))
        )
    purchases = {}
    for r in rows("purchase_items"):
        if int(r["TFPRMS"] or 0) in NON_INVOICE_TYPES:
            continue
        purchases.setdefault(r["CODE"], []).append((int(r["YR"]), num(r["QTY"]), num(r["NETVAL"])))

    def avg_cost(code, year):
        for source in (findata, purchases):
            qty = sum(q for y, q, _ in source.get(code, []) if y <= year)
            val = sum(v for y, _, v in source.get(code, []) if y <= year)
            if qty > 0 and val > 0:
                return val / qty
        return None

    expenses = {}
    for r in rows("purchase_lines"):
        if int(r["SODTYPE"] or 0) != 51 and int(r["TFPRMS"] or 0) not in NON_INVOICE_TYPES:
            expenses[r["P"]] = expenses.get(r["P"], 0.0) + num(r["NETVAL"])

    ledger = {}
    for r in rows("ledger_6x_7x"):
        year, period, acn = int(r["FISCPRD"]), int(r["PERIOD"] or 0), str(r["ACN2"])
        if not acn.startswith("6"):
            continue
        amount = num(r["DEBIT"]) - num(r["CREDIT"])
        if year == 2025:
            ledger["2025FULL"] = ledger.get("2025FULL", 0.0) + amount
        if 1 <= period <= 10:
            key = f"{year}YTD"
            ledger[key] = ledger.get(key, 0.0) + amount

    lines = [
        "ΚΕΡΔΟΣ ΕΤΑΙΡΕΙΑΣ 3000 (ποσά χωρίς ΦΠΑ, €)",
        "Περίοδος | Πωλήσεις | Κόστος πωληθέντων | Μικτό κέρδος | Μικτό % | "
        "Έξοδα (παραστ. αγορών, όχι είδη) | Καθαρό (εκτίμηση) | Έξοδα 6x λογιστικής",
    ]
    missing_notes = []
    for period in ("2025YTD", "2026YTD", "2025FULL"):
        year = int(period[:4])
        revenue = cogs = missing_value = 0.0
        missing = 0
        for r in rows("sales_items"):
            if r["P"] != period:
                continue
            value = num(r["NETVAL"])
            revenue += value
            if int(r["SODTYPE"] or 0) != 51:
                continue
            cost = avg_cost(r["CODE"], year)
            if cost is None:
                missing += 1
                missing_value += value
            else:
                cogs += cost * num(r["QTY"])
        gross = revenue - cogs
        margin = f"{gross / revenue * 100:.1f}%" if revenue else "-"
        exp = expenses.get(period, 0.0)
        led = f"{ledger[period]:.2f}" if period in ledger else "-"
        lines.append(
            f"{LABELS[period]} | {revenue:.2f} | {cogs:.2f} | {gross:.2f} | {margin} | "
            f"{exp:.2f} | {gross - exp:.2f} | {led}"
        )
        missing_notes.append(
            f"{LABELS[period]}: {missing} είδη χωρίς κόστος (πωλήσεις {missing_value:.2f} € χωρίς κόστος)"
        )
    lines.append("")
    lines.extend(missing_notes)
    lines.append("")
    lines.append("Έξοδα ανά τύπο παραστατικού αγορών (όχι είδη):")
    for r in rows("purchase_lines"):
        if int(r["SODTYPE"] or 0) != 51:
            lines.append(
                f"  {r['P']} | {r['FPRMS_NAME']} (TFPRMS {r['TFPRMS']}) | SODTYPE {r['SODTYPE']} | "
                f"{num(r['NETVAL']):.2f}"
            )
    return "\n".join(lines)


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
    data = {}
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
                data[name] = (header, rows)
                log.append(f"{name} v{index}: OK {len(rows)} γραμμές")
                break
    finally:
        conn.rollback()
        conn.close()
    (out_dir / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    report = summarize(data)
    (out_dir / "summary.txt").write_text(report + "\n", encoding="utf-8")
    print()
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
