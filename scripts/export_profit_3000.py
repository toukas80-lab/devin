"""Read-only export + profit summary for SoftOne company 3000 (2025 vs 2026, 1/1-23/10)."""

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
BASE_JOINS = """
FROM dbo.MTRLINES l
JOIN dbo.FINDOC f ON f.FINDOC = l.FINDOC
JOIN dbo.FPRMS p ON p.FPRMS = f.FPRMS AND p.COMPANY = f.COMPANY AND p.SOSOURCE = f.SOSOURCE
JOIN dbo.MTRL m ON m.MTRL = l.MTRL AND m.COMPANY = f.COMPANY"""

QUERIES = {
    "sales_items": f"""
SELECT per.P, p.NAME AS FPRMS_NAME, p.TFPRMS, m.CODE, m.SODTYPE,
       CAST(SUM(l.QTY1) AS decimal(18,3)) AS QTY,
       CAST(SUM(l.LINEVAL) AS decimal(18,2)) AS NETVAL
{BASE_JOINS}
JOIN {PERIODS} ON f.TRNDATE >= per.D1 AND f.TRNDATE < per.D2
WHERE f.COMPANY = 3000 AND f.SOSOURCE = 1351 AND f.ISCANCEL = 0
  AND p.TFPRMS IN (102,103,131,151,152,181)
GROUP BY per.P, p.NAME, p.TFPRMS, m.CODE, m.SODTYPE
ORDER BY 1, 2, 4""",
    "docs_overview": f"""
SELECT per.P, f.SOSOURCE, p.NAME AS FPRMS_NAME, p.TFPRMS, COUNT(*) AS DOCS,
       CAST(SUM(f.NETAMNT) AS decimal(18,2)) AS NETAMNT,
       CAST(SUM(f.VATAMNT) AS decimal(18,2)) AS VATAMNT,
       CAST(SUM(f.SUMAMNT) AS decimal(18,2)) AS SUMAMNT
FROM dbo.FINDOC f
JOIN dbo.FPRMS p ON p.FPRMS = f.FPRMS AND p.COMPANY = f.COMPANY AND p.SOSOURCE = f.SOSOURCE
JOIN {PERIODS} ON f.TRNDATE >= per.D1 AND f.TRNDATE < per.D2
WHERE f.COMPANY = 3000 AND f.ISCANCEL = 0
GROUP BY per.P, f.SOSOURCE, p.NAME, p.TFPRMS
ORDER BY 1, 2, 4""",
    "purchase_items": f"""
SELECT YEAR(f.TRNDATE) AS YR, p.NAME AS FPRMS_NAME, p.TFPRMS, m.CODE,
       CAST(SUM(l.QTY1) AS decimal(18,3)) AS QTY,
       CAST(SUM(l.LINEVAL) AS decimal(18,2)) AS NETVAL
{BASE_JOINS}
WHERE f.COMPANY = 3000 AND f.SOSOURCE = 1251 AND f.ISCANCEL = 0 AND m.SODTYPE = 51
  AND p.TFPRMS IN (102,103,151,152)
  AND f.TRNDATE >= '2018-01-01' AND f.TRNDATE < '2026-10-24'
GROUP BY YEAR(f.TRNDATE), p.NAME, p.TFPRMS, m.CODE
ORDER BY 1, 2, 4""",
}

LABELS = {"2025YTD": "2025 (1/1-23/10)", "2026YTD": "2026 (1/1-23/10)", "2025FULL": "2025 (όλο)"}


def num(value) -> float:
    return float(value or 0)


def tfprms(row) -> int:
    return int(row.get("TFPRMS") or 0)


def is_proforma(row) -> bool:
    return "Προτιμολόγιο" in (row.get("FPRMS_NAME") or "")


def sales_sign(row) -> int:
    name = row.get("FPRMS_NAME") or ""
    if tfprms(row) in (151, 152, 181) or "Ακυρωτικό" in name or "Επιστροφ" in name:
        return -1
    return 1


def purchase_sign(row) -> int:
    name = row.get("FPRMS_NAME") or ""
    return -1 if tfprms(row) in (151, 152) or "Πιστωτικό" in name else 1


def summarize(data: dict) -> str:
    def rows(name):
        header, body = data.get(name, ([], []))
        return [dict(zip(header, r, strict=False)) for r in body]

    purchases = {}
    for r in rows("purchase_items"):
        if is_proforma(r):
            continue
        sign = purchase_sign(r)
        purchases.setdefault(r["CODE"], []).append(
            (int(r["YR"]), sign * num(r["QTY"]), sign * num(r["NETVAL"]))
        )

    def avg_cost(code, year):
        qty = sum(q for y, q, _ in purchases.get(code, []) if y <= year)
        val = sum(v for y, _, v in purchases.get(code, []) if y <= year)
        return val / qty if qty > 0 and val > 0 else None

    expenses = {}
    for r in rows("docs_overview"):
        if int(r["SOSOURCE"]) == 1653:
            sign = -1 if "Πιστωτικό" in (r["FPRMS_NAME"] or "") else 1
            expenses[r["P"]] = expenses.get(r["P"], 0.0) + sign * num(r["NETAMNT"])

    lines = [
        "ΚΕΡΔΟΣ ΕΤΑΙΡΕΙΑΣ 3000 (ποσά χωρίς ΦΠΑ, €)",
        "Περίοδος | Πωλήσεις | Κόστος πωληθέντων | Μικτό κέρδος | Μικτό % | "
        "Έξοδα (Δαπάνες 1653) | Καθαρό (εκτίμηση)",
    ]
    notes = []
    for period in ("2025YTD", "2026YTD", "2025FULL"):
        year = int(period[:4])
        revenue = cogs = missing_value = proforma = 0.0
        missing = {}
        for r in rows("sales_items"):
            if r["P"] != period:
                continue
            if is_proforma(r):
                proforma += num(r["NETVAL"])
                continue
            sign = sales_sign(r)
            value = sign * num(r["NETVAL"])
            revenue += value
            if int(r["SODTYPE"] or 0) != 51:
                continue
            cost = avg_cost(r["CODE"], year)
            if cost is None:
                missing[r["CODE"]] = missing.get(r["CODE"], 0.0) + value
                missing_value += value
            else:
                cogs += cost * sign * num(r["QTY"])
        gross = revenue - cogs
        margin = f"{gross / revenue * 100:.1f}%" if revenue else "-"
        exp = expenses.get(period, 0.0)
        lines.append(
            f"{LABELS[period]} | {revenue:.2f} | {cogs:.2f} | {gross:.2f} | {margin} | "
            f"{exp:.2f} | {gross - exp:.2f}"
        )
        notes.append(
            f"{LABELS[period]}: {len(missing)} είδη χωρίς κόστος αγοράς "
            f"(πωλήσεις τους {missing_value:.2f}), προτιμολόγια εκτός: {proforma:.2f}"
        )
        top = sorted(missing.items(), key=lambda kv: -kv[1])[:5]
        notes.append("   χωρίς κόστος (top 5): " + ", ".join(f"{c}={v:.0f}" for c, v in top))
    return "\n".join(lines + [""] + notes)


def export_mtrl_prices(conn, out_dir: Path, log: list) -> None:
    cols = [
        r[0]
        for r in conn.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'MTRL' "
            "AND DATA_TYPE IN ('float','real','money','decimal','numeric') "
            "AND (COLUMN_NAME LIKE '%PRIC%' OR COLUMN_NAME LIKE '%COST%' OR COLUMN_NAME LIKE '%PUR%')"
        ).fetchall()
    ]
    if not cols:
        log.append("mtrl_prices: καμία στήλη τιμής/κόστους")
        return
    select = ", ".join(f"[{c}]" for c in cols)
    cursor = conn.execute(
        f"SELECT CODE, NAME, {select} FROM dbo.MTRL WHERE COMPANY = 3000 AND SODTYPE = 51 ORDER BY CODE"
    )
    rows = cursor.fetchall()
    with open(out_dir / "mtrl_prices.csv", "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow([c[0] for c in cursor.description])
        writer.writerows(["" if v is None else v for v in row] for row in rows)
    log.append(f"mtrl_prices: OK {len(rows)} γραμμές, στήλες {', '.join(cols)}")


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


def load_csv(out_dir: Path) -> dict:
    data = {}
    for name in QUERIES:
        path = out_dir / f"{name}.csv"
        if path.exists():
            with open(path, encoding="utf-8-sig", newline="") as fh:
                reader = csv.reader(fh, delimiter=";")
                header = next(reader)
                data[name] = (header, list(reader))
    return data


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data/profit")
    out_dir.mkdir(parents=True, exist_ok=True)
    if "--offline" in sys.argv:
        print(summarize(load_csv(out_dir)))
        return 0
    log = []
    data = {}
    conn = connect()
    try:
        for name, sql in QUERIES.items():
            try:
                cursor = conn.execute(sql)
                rows = cursor.fetchall()
                header = [col[0] for col in cursor.description]
            except pyodbc.Error as exc:
                log.append(f"{name}: ΣΦΑΛΜΑ {exc}")
                conn.rollback()
                continue
            data[name] = (header, rows)
            with open(out_dir / f"{name}.csv", "w", encoding="utf-8-sig", newline="") as fh:
                writer = csv.writer(fh, delimiter=";")
                writer.writerow(header)
                writer.writerows(["" if v is None else v for v in row] for row in rows)
            log.append(f"{name}: OK {len(rows)} γραμμές")
        try:
            export_mtrl_prices(conn, out_dir, log)
        except pyodbc.Error as exc:
            log.append(f"mtrl_prices: ΣΦΑΛΜΑ {exc}")
            conn.rollback()
    finally:
        conn.rollback()
        conn.close()
    report = summarize(data)
    (out_dir / "run_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    (out_dir / "summary.txt").write_text(report + "\n", encoding="utf-8")
    print("\n".join(log))
    print()
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
