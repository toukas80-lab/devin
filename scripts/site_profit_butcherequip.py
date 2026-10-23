"""butcherequip.gr profit: site order lines (data/profit/site_lines.csv) x SoftOne 3000 avg purchase cost.

Read-only SQL. Usage: python scripts/site_profit_butcherequip.py [--courier 0] [--card-fee 0]
--courier: real courier cost per order in € (excl. VAT); --card-fee: % fee on card/PayPal orders.
"""

import argparse
import csv
import os
from pathlib import Path

DATA = Path("data/profit")
VAT = 1.24
LABELS = {"2025YTD": "2025 (1/1-23/10)", "2026YTD": "2026 (1/1-23/10)", "2025FULL": "2025 (όλο)"}

COST_SQL = """
SELECT YEAR(f.TRNDATE) AS YR, p.NAME, p.TFPRMS, m.CODE,
       CAST(SUM(l.QTY1) AS decimal(18,3)) AS QTY, CAST(SUM(l.LINEVAL) AS decimal(18,2)) AS NETVAL
FROM dbo.MTRLINES l
JOIN dbo.FINDOC f ON f.FINDOC = l.FINDOC
JOIN dbo.FPRMS p ON p.FPRMS = f.FPRMS AND p.COMPANY = f.COMPANY AND p.SOSOURCE = f.SOSOURCE
JOIN dbo.MTRL m ON m.MTRL = l.MTRL AND m.COMPANY = f.COMPANY
WHERE f.COMPANY = 3000 AND f.SOSOURCE = 1251 AND f.ISCANCEL = 0 AND m.SODTYPE = 51
  AND p.TFPRMS IN (102,103,151,152) AND f.TRNDATE < '2026-10-24'
GROUP BY YEAR(f.TRNDATE), p.NAME, p.TFPRMS, m.CODE"""


def read(name):
    with open(DATA / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def load_purchases(rows) -> dict:
    purchases = {}
    for yr, name, tfprms, code, qty, val in rows:
        if "Προτιμολόγιο" in (name or ""):
            continue
        sign = -1 if int(tfprms) in (151, 152) or "Πιστωτικό" in (name or "") else 1
        purchases.setdefault(str(code), []).append((int(yr), sign * float(qty), sign * float(val)))
    return purchases


def fetch_purchases() -> dict:
    import pyodbc

    password = os.environ["SQLCMDPASSWORD"]
    last = None
    for driver in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        try:
            conn = pyodbc.connect(
                f"DRIVER={{{driver}}};SERVER=.\\SOFTONE;DATABASE=FOUNTOUKAS;"
                f"UID=devin_ro;PWD={password};TrustServerCertificate=yes;",
                timeout=30,
                autocommit=False,
            )
            break
        except pyodbc.Error as exc:
            last = exc
    else:
        raise SystemExit(f"Αποτυχία σύνδεσης: {last}")
    try:
        return load_purchases(conn.execute(COST_SQL).fetchall())
    finally:
        conn.rollback()
        conn.close()


def report(purchases: dict, courier: float, card_fee: float) -> str:
    def avg_cost(code, year):
        qty = sum(q for y, q, _ in purchases.get(code, []) if y <= year)
        val = sum(v for y, _, v in purchases.get(code, []) if y <= year)
        return val / qty if qty > 0 and val > 0 else None

    lines_rows, orders_rows = read("site_lines.csv"), read("site_orders.csv")
    out = [
        "ΚΕΡΔΟΣ BUTCHEREQUIP.GR (ολοκληρωμένες παραγγελίες, ποσά χωρίς ΦΠΑ 24%, €)",
        "Περίοδος | Παραγγελίες | Πωλήσεις ειδών | Κόστος ειδών | Μικτό κέρδος | Μικτό % | "
        "Μεταφορικά πελάτη | Courier | Προμήθειες καρτών | Καθαρό κέρδος",
    ]
    notes = []
    for period in ("2025YTD", "2026YTD", "2025FULL"):
        year = int(period[:4])
        orders = [o for o in orders_rows if o["P"] == period]
        sales = cogs = 0.0
        missing, suspect = {}, {}
        for li in (r for r in lines_rows if r["P"] == period):
            value = float(li["TOTAL_INCL_VAT"]) / VAT
            sales += value
            sku = li["SKU"].strip()
            sku = sku.zfill(5) if sku.isdigit() else sku
            cost = avg_cost(sku, year) if sku else None
            line_cost = cost * float(li["QTY"]) if cost is not None else None
            if cost is None:
                key = sku or li["NAME"][:30]
                missing[key] = missing.get(key, 0.0) + value
            elif line_cost > 3 * value:
                suspect[sku] = f"κόστος {cost:.2f}/τεμ vs τιμή {value / float(li['QTY']):.2f}"
                missing[sku] = missing.get(sku, 0.0) + value
            else:
                cogs += line_cost
        shipping = sum(float(o["SHIPPING_INCL_VAT"]) for o in orders) / VAT
        courier_total = courier * len(orders)
        fees = sum(
            float(o["TOTAL_INCL_VAT"]) * card_fee / 100
            for o in orders
            if o["PAYMENT"] not in ("cod", "bacs")
        )
        gross = sales - cogs
        margin = f"{gross / sales * 100:.1f}%" if sales else "-"
        net = gross + shipping - courier_total - fees
        out.append(
            f"{LABELS[period]} | {len(orders)} | {sales:.2f} | {cogs:.2f} | {gross:.2f} | {margin} | "
            f"{shipping:.2f} | {courier_total:.2f} | {fees:.2f} | {net:.2f}"
        )
        top = sorted(missing.items(), key=lambda kv: -kv[1])
        notes.append(
            f"{LABELS[period]}: {len(missing)} είδη χωρίς κόστος στο SoftOne "
            f"(πωλήσεις {sum(missing.values()):.2f}): "
            + ", ".join(f"{k}={v:.0f}" for k, v in top[:8])
        )
        for sku, why in suspect.items():
            notes.append(f"   {sku}: ύποπτο κόστος (μονάδα μέτρησης;) {why} — εκτός κόστους")
    out += ["", *notes, ""]
    out.append(f"Παράμετροι: courier {courier:.2f} €/παραγγελία, προμήθεια καρτών {card_fee:.2f}%.")
    out.append("Δεν περιλαμβάνονται: διαφήμιση, hosting, συσκευασία, χρόνος.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--courier", type=float, default=0.0)
    parser.add_argument("--card-fee", type=float, default=0.0)
    args = parser.parse_args()
    text = report(fetch_purchases(), args.courier, args.card_fee)
    (DATA / "site_profit_summary.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
