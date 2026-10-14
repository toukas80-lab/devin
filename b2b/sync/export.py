"""B2B-25: SoftOne (FOUNTOUKAS, COMPANY=1001 — απόθεμα από STOCK_COMPANY κατά CODE είδους, read-only) -> b2b/out/*.json.
B2B-33: είδη μόνο από catalog_codes.txt."""
import json
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

import pyodbc

COMPANY = 1001
STOCK_COMPANY = 3000
EXCLUDE_GROUPS = ("SCRAP",)
OUT_DIR = Path(__file__).resolve().parent.parent / "out"
CATALOG_FILE = Path(__file__).resolve().parent / "catalog_codes.txt"
CATALOG_CODES = (
    {ln.strip() for ln in CATALOG_FILE.read_text(encoding="utf-8").splitlines()
     if ln.strip()}
    if CATALOG_FILE.exists() else set()
)
CHAPTERS_FILE = Path(__file__).resolve().parent / "catalog_chapters.tsv"
CATALOG_CHAPTERS = (
    {p[0].strip(): p[1].strip()
     for ln in CHAPTERS_FILE.read_text(encoding="utf-8").splitlines()
     if ln.strip()
     for p in [ln.split("\t", 1)] if len(p) == 2}
    if CHAPTERS_FILE.exists() else {}
)
CUTOFF36 = "DATEADD(month,-36,CAST(GETDATE() AS date))"
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


def _sql_list(vals):
    return ", ".join("'" + str(v).replace("'", "''") + "'" for v in vals)


_EXCL_GRP_SQL = _sql_list(EXCLUDE_GROUPS)

Q_ITEMS = f"""
SELECT m.MTRL AS id, m.CODE AS code, m.NAME AS name, m.MTRGROUP AS group_id,
       ISNULL(u.NAME,'') AS unit,
       CAST(ISNULL(v.PERCNT,0) AS float) AS vat_pct,
       CAST(ISNULL(m.PRICEW,0) AS float) AS price_w,
       CAST(ISNULL(m.PRICER,0) AS float) AS price_r,
       CAST(ISNULL((SELECT TOP 1 d.QTY1 FROM dbo.MTRL s JOIN dbo.MTRDATA d
                    ON d.MTRL=s.MTRL AND d.COMPANY=s.COMPANY
                    WHERE s.COMPANY={STOCK_COMPANY} AND s.SODTYPE=51
                      AND s.CODE=m.CODE
                    ORDER BY d.FISCPRD DESC),0) AS float) AS stock,
       ISNULL(mf.NAME,'') AS manufacturer,
       ISNULL(m.WEBPAGE,'') AS webpage,
       m.VAT AS vat_code, m.MTRUNIT1 AS mtrunit
FROM dbo.MTRL m
LEFT JOIN dbo.MTRUNIT u ON u.MTRUNIT=m.MTRUNIT1 AND u.COMPANY=m.COMPANY
LEFT JOIN dbo.VAT v ON v.VAT=m.VAT
LEFT JOIN dbo.MTRMANFCTR mf ON mf.MTRMANFCTR=m.MTRMANFCTR AND mf.COMPANY=m.COMPANY
WHERE m.COMPANY={COMPANY} AND m.SODTYPE=51 AND m.ISACTIVE=1
  AND NULLIF(LTRIM(RTRIM(ISNULL(m.WEBPAGE,''))),'') IS NOT NULL
  AND UPPER(LTRIM(RTRIM(ISNULL((SELECT g.NAME FROM dbo.MTRGROUP g
              WHERE g.COMPANY=m.COMPANY AND g.MTRGROUP=m.MTRGROUP),''))))
      NOT IN ({_EXCL_GRP_SQL})
ORDER BY m.CODE
"""

Q_GROUPS = f"""
SELECT g.MTRGROUP AS id, g.NAME AS name
FROM dbo.MTRGROUP g
WHERE g.COMPANY={COMPANY}
  AND EXISTS (SELECT 1 FROM dbo.MTRL m
              WHERE m.COMPANY={COMPANY} AND m.SODTYPE=51 AND m.ISACTIVE=1
                AND m.MTRGROUP=g.MTRGROUP)
ORDER BY g.NAME
"""

Q_CUSTOMERS = f"""
SELECT t.TRDR AS id, t.CODE AS code, t.NAME AS name,
       ISNULL(t.EMAIL,'') AS email, ISNULL(t.AFM,'') AS afm,
       t.PAYMENT AS payment
FROM dbo.TRDR t
WHERE t.COMPANY={COMPANY} AND t.SODTYPE=13 AND t.ISACTIVE=1
ORDER BY t.CODE
"""

Q_BALANCES = f"""
SELECT t.TRDR AS id, SUM({SIGN}) AS bal
FROM dbo.TRDTRN t {TP_JOIN}
WHERE t.COMPANY={COMPANY} AND t.SODTYPE=13
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
  WHERE f.COMPANY={COMPANY} AND f.SOSOURCE=1351 AND f.ISCANCEL=0
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
       CASE WHEN {SIGN} > 0 THEN {SIGN} ELSE 0 END AS debit,
       CASE WHEN {SIGN} < 0 THEN -({SIGN}) ELSE 0 END AS credit
FROM dbo.TRDTRN t {TP_JOIN}
WHERE t.COMPANY={COMPANY} AND t.SODTYPE=13
  AND t.TRNDATE >= {CUTOFF36}
ORDER BY t.TRDR, t.TRNDATE, t.FINDOC, t.TRDTRN
"""

Q_OPENING = f"""
SELECT t.TRDR AS customer_id, SUM({SIGN}) AS opening
FROM dbo.TRDTRN t {TP_JOIN}
WHERE t.COMPANY={COMPANY} AND t.SODTYPE=13
  AND t.TRNDATE < {CUTOFF36}
GROUP BY t.TRDR
"""

Q_INVOICES = f"""
SELECT f.FINDOC AS findoc_id, f.TRDR AS customer_id,
       CAST(f.TRNDATE AS date) AS date, f.FINCODE AS doc,
       CAST(f.NETAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END AS float) AS net,
       CAST(f.VATAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END AS float) AS vat,
       CAST(f.SUMAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END AS float) AS total,
       ISNULL(md.SOSIGNQR,'') AS einv_url
FROM dbo.FINDOC f
JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
LEFT JOIN dbo.MTRDOC md ON md.FINDOC=f.FINDOC
WHERE f.COMPANY={COMPANY} AND f.SOSOURCE=1351 AND f.ISCANCEL=0
  AND p.TFPRMS IN (102,103,131,151,152,181)
  AND f.TRNDATE >= {CUTOFF36}
ORDER BY f.TRDR, f.TRNDATE, f.FINDOC
"""

Q_BALSHEET = f"""
SELECT b.TRDR AS id, SUM(b.LDEBIT - b.LCREDIT) AS bal
FROM dbo.TRDBALSHEET b
WHERE b.COMPANY={COMPANY}
GROUP BY b.TRDR
"""

# B2B-49: ΠΑΡ σειράς 7021 με COMMENTS 'B2B W-######' → κατάσταση παραγγελίας πύλης.
Q_ORDER_STATUS = f"""
SELECT f.COMMENTS AS comments, f.FINCODE AS fincode, f.FULLYTRANSF AS fullytransf
FROM dbo.FINDOC f
WHERE f.COMPANY={COMPANY} AND f.SOSOURCE=1351 AND f.SERIES=7021 AND f.ISCANCEL=0
  AND f.TRNDATE >= '2026-10-14' AND f.COMMENTS LIKE 'B2B W-%'
"""

WNO_RE = re.compile(r"W-\d{6}")


def order_status_rows(raw):
    """FINDOC γραμμές -> [{order_no, fincode, done}].

    done=1 αν έστω ένα FINDOC του order_no έχει FULLYTRANSF=1.
    """
    ostat = {}
    for r in raw:
        m = WNO_RE.search(str(r.get("comments") or ""))
        if not m:
            continue
        e = ostat.setdefault(m.group(0),
                             {"order_no": m.group(0), "fincode": "", "done": 0})
        if r.get("fincode"):
            e["fincode"] = r["fincode"]
        if r.get("fullytransf"):
            e["done"] = 1
    return list(ostat.values())


DRIVE_ID_RE = re.compile(r"(?:/d/|[?&]id=)([A-Za-z0-9_-]{20,})")
EINV_PREFIXES = ("https://einvoice.impact.gr/p/",
                 "https://einvoice.s1ecos.gr/p/")


def drive_id(url):
    m = DRIVE_ID_RE.search(str(url or ""))
    return m.group(1) if m else ""


def einv_url(v):
    u = str(v or "")
    return u if u.startswith(EINV_PREFIXES) and len(u) <= 255 else ""


def norm_afm(v):
    a = re.sub(r"[\s .\-]+", "", str(v or "")).upper()
    a = re.sub(r"^(E|Ε)(L|Λ)", "", a)
    if re.fullmatch(r"\d{8}", a):
        a = "0" + a
    if not re.fullmatch(r"\d{9}", a) or a == "0" * 9:
        return ""
    s = sum(int(a[i]) << (8 - i) for i in range(8))
    return a if s % 11 % 10 == int(a[8]) else ""


def rows(cur, sql):
    return [dict(zip([c[0] for c in cur.description], r)) for r in cur.execute(sql)]


def dump(name, data):
    path = OUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return f"{name}.json: {len(data)} rows, {path.stat().st_size / 1024:.1f} KB"


def main():
    t0 = time.time()
    if len(CATALOG_CODES) < 100:
        sys.exit(f"catalog_codes.txt missing or has <100 codes ({len(CATALOG_CODES)})")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cn = pyodbc.connect(CONN_STR)
    cur = cn.cursor()

    out = []
    items = rows(cur, Q_ITEMS)
    items = [it for it in items if str(it["code"]).strip() in CATALOG_CODES]
    for it in items:
        it["photo"] = drive_id(it.pop("webpage"))
        it["chapter"] = CATALOG_CHAPTERS.get(str(it["code"]).strip(), "")
    manfs = {it["manufacturer"] for it in items if it["manufacturer"]}
    print(f"items: {len(items)} | manufacturers: {len(manfs)} | "
          f"no manufacturer: {len(items) - sum(1 for i in items if i['manufacturer'])}")
    out.append(dump("items", items))
    keep_gids = {it["group_id"] for it in items}
    excl_g = {g.upper().strip() for g in EXCLUDE_GROUPS}
    groups = [g for g in rows(cur, Q_GROUPS)
              if g["id"] in keep_gids
              and str(g["name"]).upper().strip() not in excl_g]
    out.append(dump("groups", groups))

    raw = rows(cur, Q_CUSTOMERS)
    n_active = len(raw)
    for c in raw:
        c["afm"] = norm_afm(c["afm"])
    customers = [c for c in raw if c["afm"]]
    n_bad_afm = n_active - len(customers)
    cnt = Counter(c["afm"] for c in customers)
    dup = {a for a, n in cnt.items() if n > 1}
    n_dup = sum(1 for c in customers if c["afm"] in dup)
    customers = [c for c in customers if c["afm"] not in dup]
    print(f"customers: {n_active} active, {n_bad_afm} invalid/blank AFM, "
          f"{n_dup} duplicate-AFM removed ({len(dup)} AFMs)")

    balances = {r["id"]: round(r["bal"] or 0, 2) for r in rows(cur, Q_BALANCES)}
    for c in customers:
        c["balance"] = balances.get(c["id"], 0.0)
    out.append(dump("customers", customers))
    cust_ids = {c["id"] for c in customers}

    item_ids = {it["id"] for it in items}
    prices = [r for r in rows(cur, Q_PRICES)
              if r["customer_id"] in cust_ids and r["item_id"] in item_ids]
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
        f"SELECT CAST({CUTOFF36} AS date)").fetchone()[0])
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

    inv_rows = rows(cur, Q_INVOICES)
    if len({r["findoc_id"] for r in inv_rows}) != len(inv_rows):
        sys.exit("duplicate findoc_id in Q_INVOICES (MTRDOC join) — STOP")
    invoices = [r for r in inv_rows if r["customer_id"] in cust_ids]
    for r in invoices:
        r["date"] = r["date"].isoformat()
        for k in ("net", "vat", "total"):
            r[k] = round(r[k], 2)
        r["einv_url"] = einv_url(r["einv_url"])
    out.append(dump("invoices", invoices))

    out.append(dump("order_status",
                    order_status_rows(rows(cur, Q_ORDER_STATUS))))

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
