"""B2B-02: SoftOne (FOUNTOUKAS, COMPANY=3000, read-only) -> b2b/out/*.json."""
import json
import os
import random
import sys
import time
from pathlib import Path

import pyodbc

COMPANY = 3000
OUT_DIR = Path(__file__).resolve().parent.parent / "out"
CUTOFF24 = "DATEADD(month,-24,CAST(GETDATE() AS date))"
CUTOFF12 = "DATEADD(month,-12,CAST(GETDATE() AS date))"

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.\\SOFTONE;DATABASE=FOUNTOUKAS;"
    f"UID=devin_ro;PWD={os.environ.get('SQLCMDPASSWORD', '')}"
)

SIGN = (
    "CASE WHEN ISNULL(tp.f1,0)=1 OR ISNULL(tp.f2,0)=-1 THEN t.TRNVAL"
    " WHEN ISNULL(tp.f2,0)=1 OR ISNULL(tp.f1,0)=-1 THEN -t.TRNVAL ELSE 0 END"
)
TP_JOIN = (
    "LEFT JOIN (SELECT TPRMS, MAX(FLG01) f1, MAX(FLG02) f2"
    "           FROM dbo.TPRMS WHERE SODTYPE=13 GROUP BY TPRMS) tp"
    " ON tp.TPRMS=t.TPRMS"
)

Q_ITEMS = """
SELECT m.MTRL AS id, m.CODE AS code, m.NAME AS name, m.MTRGROUP AS group_id,
       ISNULL(u.NAME,'') AS unit,
       CAST(ISNULL(v.PERCNT,0) AS float) AS vat_pct,
       CAST(ISNULL(m.PRICEW,0) AS float) AS price_w,
       CAST(ISNULL((SELECT TOP 1 d.QTY1 FROM dbo.MTRDATA d
                    WHERE d.MTRL=m.MTRL AND d.COMPANY=m.COMPANY
                    ORDER BY d.FISCPRD DESC),0) AS float) AS stock
FROM dbo.MTRL m
LEFT JOIN dbo.MTRUNIT u ON u.MTRUNIT=m.MTRUNIT1 AND u.COMPANY=m.COMPANY
LEFT JOIN dbo.VAT v ON v.VAT=m.VAT
WHERE m.COMPANY=3000 AND m.SODTYPE=51 AND m.ISACTIVE=1
ORDER BY m.CODE
"""

Q_GROUPS = """
SELECT g.MTRGROUP AS id, g.NAME AS name
FROM dbo.MTRGROUP g
WHERE g.COMPANY=3000
  AND EXISTS (SELECT 1 FROM dbo.MTRL m
              WHERE m.COMPANY=3000 AND m.SODTYPE=51 AND m.ISACTIVE=1
                AND m.MTRGROUP=g.MTRGROUP)
ORDER BY g.NAME
"""

Q_CUSTOMERS = f"""
SELECT t.TRDR AS id, t.CODE AS code, t.NAME AS name, ISNULL(t.EMAIL,'') AS email
FROM dbo.TRDR t
WHERE t.COMPANY=3000 AND t.SODTYPE=13 AND t.ISACTIVE=1
  AND EXISTS (
    SELECT 1 FROM dbo.FINDOC f
    JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
    WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.ISCANCEL=0
      AND p.TFPRMS IN (102,103,131,151,152,181)
      AND f.TRNDATE >= {CUTOFF24}
      AND f.TRDR = t.TRDR)
ORDER BY t.CODE
"""

Q_BALANCES = f"""
SELECT t.TRDR AS id, SUM({SIGN}) AS bal
FROM dbo.TRDTRN t {TP_JOIN}
WHERE t.COMPANY=3000 AND t.SODTYPE=13
GROUP BY t.TRDR
"""

Q_PRICES = f"""
SELECT x.customer_id, x.item_id, x.price, x.date
FROM (
  SELECT f.TRDR AS customer_id, l.MTRL AS item_id,
         CAST(l.LINEVAL/NULLIF(l.QTY1,0) AS float) AS price,
         CAST(f.TRNDATE AS date) AS date,
         ROW_NUMBER() OVER (PARTITION BY f.TRDR, l.MTRL
                            ORDER BY f.TRNDATE DESC, f.FINDOC DESC) AS rn
  FROM dbo.MTRLINES l
  JOIN dbo.FINDOC f ON f.FINDOC=l.FINDOC
  JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
  WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.ISCANCEL=0
    AND p.TFPRMS IN (102,103)
    AND f.TRNDATE >= {CUTOFF12}
    AND l.QTY1>0 AND l.LINEVAL>0
) x
WHERE x.rn=1
ORDER BY x.customer_id, x.item_id
"""

Q_LEDGER = f"""
SELECT t.TRDR AS customer_id, CAST(t.TRNDATE AS date) AS date,
       ISNULL(t.FINCODE,'') AS doc, ISNULL(t.COMMENTS,'') AS descr,
       CASE WHEN {SIGN} > 0 THEN t.TRNVAL ELSE 0 END AS debit,
       CASE WHEN {SIGN} < 0 THEN t.TRNVAL ELSE 0 END AS credit
FROM dbo.TRDTRN t {TP_JOIN}
WHERE t.COMPANY=3000 AND t.SODTYPE=13
  AND t.TRNDATE >= {CUTOFF24}
ORDER BY t.TRDR, t.TRNDATE, t.FINDOC, t.TRDTRN
"""

Q_OPENING = f"""
SELECT t.TRDR AS customer_id, SUM({SIGN}) AS opening
FROM dbo.TRDTRN t {TP_JOIN}
WHERE t.COMPANY=3000 AND t.SODTYPE=13
  AND t.TRNDATE < {CUTOFF24}
GROUP BY t.TRDR
"""

Q_INVOICES = f"""
SELECT f.FINDOC AS findoc_id, f.TRDR AS customer_id,
       CAST(f.TRNDATE AS date) AS date, f.FINCODE AS doc,
       CAST(f.NETAMNT * CASE WHEN p.TFPRMS IN (151,152) THEN -1 ELSE 1 END AS float) AS net,
       CAST(f.VATAMNT * CASE WHEN p.TFPRMS IN (151,152) THEN -1 ELSE 1 END AS float) AS vat,
       CAST(f.SUMAMNT * CASE WHEN p.TFPRMS IN (151,152) THEN -1 ELSE 1 END AS float) AS total
FROM dbo.FINDOC f
JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.ISCANCEL=0
  AND p.TFPRMS IN (102,103,151,152)
  AND f.TRNDATE >= {CUTOFF24}
ORDER BY f.TRDR, f.TRNDATE, f.FINDOC
"""

Q_BALSHEET = """
SELECT b.TRDR AS id, SUM(b.LDEBIT - b.LCREDIT) AS bal
FROM dbo.TRDBALSHEET b
WHERE b.COMPANY=3000
GROUP BY b.TRDR
"""


def rows(cur, sql):
    return [dict(zip([c[0] for c in cur.description], r)) for r in cur.execute(sql)]


def dump(name, data):
    path = OUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return f"{name}.json: {len(data)} rows, {path.stat().st_size / 1024:.1f} KB"


def main():
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cn = pyodbc.connect(CONN_STR)
    cur = cn.cursor()

    out = []
    out.append(dump("items", rows(cur, Q_ITEMS)))
    out.append(dump("groups", rows(cur, Q_GROUPS)))

    customers = rows(cur, Q_CUSTOMERS)
    balances = {r["id"]: round(r["bal"] or 0, 2) for r in rows(cur, Q_BALANCES)}
    for c in customers:
        c["balance"] = balances.get(c["id"], 0.0)
    out.append(dump("customers", customers))
    cust_ids = {c["id"] for c in customers}

    prices = [r for r in rows(cur, Q_PRICES) if r["customer_id"] in cust_ids]
    for r in prices:
        r["price"] = round(r["price"], 4)
        r["date"] = r["date"].isoformat()
    out.append(dump("prices", prices))

    ledger = [r for r in rows(cur, Q_LEDGER) if r["customer_id"] in cust_ids]
    for r in ledger:
        r["date"] = r["date"].isoformat()
        r["debit"] = round(r["debit"], 2)
        r["credit"] = round(r["credit"], 2)
    cutoff = str(cur.execute(
        f"SELECT CAST({CUTOFF24} AS date)").fetchone()[0])
    openings = {r["customer_id"]: round(r["opening"] or 0, 2)
                for r in rows(cur, Q_OPENING)}
    for cid, ob in sorted(openings.items()):
        if cid in cust_ids and abs(ob) > 0.004:
            ledger.insert(0, {
                "customer_id": cid, "date": cutoff, "doc": "",
                "descr": "Υπόλοιπο μεταφοράς",
                "debit": ob if ob > 0 else 0.0,
                "credit": -ob if ob < 0 else 0.0,
                "opening": True})
    ledger.sort(key=lambda r: (r["customer_id"],
                               not r.get("opening"), r["date"], r["doc"]))
    out.append(dump("ledger", ledger))

    invoices = [r for r in rows(cur, Q_INVOICES) if r["customer_id"] in cust_ids]
    for r in invoices:
        r["date"] = r["date"].isoformat()
        for k in ("net", "vat", "total"):
            r[k] = round(r[k], 2)
    out.append(dump("invoices", invoices))

    sample = random.Random().sample(sorted(cust_ids), min(3, len(cust_ids)))
    bs = {r["id"]: r["bal"] for r in rows(cur, Q_BALSHEET)}
    bal_ok = sum(abs(balances.get(c, 0) - round(bs.get(c, 0) or 0, 2)) < 0.05
                 for c in sample)
    flow_ok = sum(
        abs(openings.get(c, 0)
            + sum(r["debit"] - r["credit"] for r in ledger
                  if r["customer_id"] == c and not r.get("opening"))
            - balances.get(c, 0)) < 0.05
        for c in sample)

    print("\n".join(out))
    print(f"Elapsed: {time.time() - t0:.1f}s")
    print(f"Check balance vs TRDBALSHEET: {bal_ok}/{len(sample)} OK")
    print(f"Check opening + moves = balance: {flow_ok}/{len(sample)} OK")
    cn.close()


if __name__ == "__main__":
    if not os.environ.get("SQLCMDPASSWORD"):
        sys.exit("SQLCMDPASSWORD env var missing")
    main()
