"""Κατάλογος κεφαλαίου από παραστατικό «Κατάλογος Χονδρικής» (ΚΑΤ...) του SoftOne, στο στήσιμο του v11.

SQL μόνο SELECT (devin_ro). Παράδειγμα:
  python build_catalog.py --fincode ΚΑΤ0000004 --date 2026-10-25 --photos "F:\\...\\Για έντυπο κατ" --out out.pdf
Χωρίς SQL:  --csv items.csv  (στήλες CODE;NAME;UNIT;PRICE, διαχωριστικό ;)
"""

import argparse
import csv
import io
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
W, H = 595, 842
L, R = 28, 567
INK = (0x21 / 255, 0x21 / 255, 0x21 / 255)
RED = (0xD1 / 255, 0x1A / 255, 0x1A / 255)
DOT = (0.82, 0.10, 0.10)
ROW_TOP, ROW_H, ROW_BOTTOM = 107, 46, 805
IMG_X0, IMG_X1, IMG_MAX_H = 28, 134, 40
FOOTER = "ΦΟΥΝΤΟΥΚΑΣ ΘΕΟΔΩΡΟΣ ΜΟΝ. ΙΚΕ ∙ 2310 227 642 ∙ info@crazysouvle.gr"
UNITS = {"ΤΕΜ": "Τεμ.", "ΚΙΛ": "Κιλά", "ΚΙΒ": "Κιβ."}

SQL_DOC = """SELECT f.FINDOC, f.COMMENTS FROM FINDOC f
WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.FINCODE=? AND CAST(f.TRNDATE AS date)=? AND f.ISCANCEL=0"""
SQL_LINES = """SELECT m.CODE, m.NAME, u.NAME AS UNIT, l.PRICE, l.COMMENTS, l.COMMENTS1
FROM MTRLINES l
JOIN MTRL m ON m.MTRL=l.MTRL AND m.COMPANY=3000
LEFT JOIN MTRUNIT u ON u.MTRUNIT=m.MTRUNIT1 AND u.COMPANY=m.COMPANY
WHERE l.FINDOC=? ORDER BY l.LINENUM"""


def register_fonts():
    pairs = [
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ),
    ]
    for reg, bold in pairs:
        if os.path.exists(reg) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("AR", reg))
            pdfmetrics.registerFont(TTFont("AB", bold))
            return
    sys.exit("Δεν βρέθηκε γραμματοσειρά Arial")


def unit_label(name):
    n = (name or "").strip().upper()
    for k, v in UNITS.items():
        if n.startswith(k):
            return v
    return name or "Τεμ."


def load_sql(fincode, date):
    import pyodbc

    cn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SOFTONE;DATABASE=FOUNTOUKAS;"
        "UID=devin_ro;PWD=" + os.environ["SQLCMDPASSWORD"]
    )
    docs = cn.execute(SQL_DOC, fincode, date).fetchall()
    if len(docs) != 1:
        sys.exit(f"ΣΤΟΠ: βρέθηκαν {len(docs)} παραστατικά {fincode} με ημερομηνία {date}")
    findoc, comments = docs[0]
    lines = cn.execute(SQL_LINES, findoc).fetchall()
    rows = [{"CODE": c, "NAME": n, "UNIT": unit_label(u), "PRICE": float(p or 0)} for c, n, u, p, *_ in lines]
    return comments, sort_by_remarks(rows, [ln[4:] for ln in lines])


def sort_by_remarks(rows, remarks):
    """Σειρά = αριθμός στις «Παρατηρήσεις» της γραμμής (00, 01, ...)· αλλιώς σειρά γραμμών."""
    for i, field in enumerate(("COMMENTS", "COMMENTS1")):
        vals = [(r[i] or "").strip() for r in remarks]
        if vals and all(v.isdigit() for v in vals):
            print(f"ΣΕΙΡΑ=MTRLINES.{field}")
            return [row for _, row in sorted(zip((int(v) for v in vals), rows), key=lambda t: t[0])]
    print("ΣΕΙΡΑ=LINENUM (οι Παρατηρήσεις δεν είναι όλες αριθμοί)")
    return rows


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [
            {
                "CODE": r["CODE"].strip(),
                "NAME": r["NAME"].strip(),
                "UNIT": unit_label(r.get("UNIT")),
                "PRICE": float((r.get("PRICE") or "0").replace(",", ".")),
            }
            for r in csv.DictReader(f, delimiter=";")
        ]


def price_text(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def photo(photos, code):
    for ext in (".jpg", ".jpeg", ".png", ".JPG", ".PNG"):
        p = Path(photos) / f"{code}{ext}"
        if p.exists():
            im = Image.open(p).convert("RGB")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            box = ImageChops.difference(im, bg).convert("L").point(lambda x: 255 if x > 18 else 0).getbbox()
            if box:
                im = im.crop(box)
            if im.width > 800:
                im = im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=88)
            buf.seek(0)
            return ImageReader(buf), im.width, im.height
    return None


def text(c, x, top, s, font, size, color=INK, align="l"):
    c.setFillColorRGB(*color)
    c.setFont(font, size)
    y = H - top - size * 0.905
    (c.drawRightString if align == "r" else c.drawString)(x, y, s)


def page_frame(c, title, section, page_no, pages, logo, legend):
    c.drawImage(logo, L, H - 55, 137.5, 44, mask="auto")
    text(c, 566.8, 18.2, title, "AB", 13, align="r")
    text(c, 566.9, 37.9, "Τιμές χωρίς ΦΠΑ", "AR", 9, RED, "r")
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(0.8)
    c.line(L, H - 60, R, H - 60)
    c.setFillColorRGB(*INK)
    c.rect(L, H - 88, R - L, 20, stroke=0, fill=1)
    text(c, 34, 72.5, section, "AB", 10.5, (1, 1, 1))
    c.setFillColorRGB(0.92, 0.92, 0.92)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.rect(L, H - 105, R - L, 15, stroke=1, fill=1)
    for x, s in ((58, "ΕΙΚΟΝΑ"), (140, "ΚΩΔΙΚΟΣ"), (186, "ΠΕΡΙΓΡΑΦΗ ΕΙΔΟΥΣ"), (464, "Μ.Μ.")):
        text(c, x, 93.2, s, "AB", 7.5)
    text(c, 562, 93.2, "ΤΙΜΗ €", "AB", 7.5, align="r")
    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.setLineWidth(0.4)
    c.line(L, H - 808, R, H - 808)
    text(c, L, 813.7, FOOTER, "AR", 7)
    if legend:
        c.setFillColorRGB(*DOT)
        c.circle(352, H - 817.5, 3, stroke=0, fill=1)
        text(c, 358, 813.7, "= καλύτερη τιμή ποσότητας", "AR", 7, RED)
    text(c, 567, 813.2, f"Σελ. {page_no} / {pages}", "AB", 7.5, align="r")


def build(rows, out, title, section, photos, dots):
    register_fonts()
    logo = ImageReader(str(HERE / "logo.png"))
    per_page = (ROW_BOTTOM - ROW_TOP) // ROW_H
    chunks = [rows[i : i + per_page] for i in range(0, len(rows), per_page)] or [[]]
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle(title + " - " + section.split(".", 1)[-1].strip())
    c.setAuthor("ΦΟΥΝΤΟΥΚΑΣ ΘΕΟΔΩΡΟΣ ΜΟΝ. ΙΚΕ")
    missing = []
    for n, chunk in enumerate(chunks, 1):
        sec = section if n == 1 else section + " (συνέχεια)"
        page_frame(c, title, sec, n, len(chunks), logo, bool(dots))
        for i, r in enumerate(chunk):
            top = ROW_TOP + i * ROW_H
            mid = top + ROW_H / 2
            ph = photo(photos, r["CODE"]) if photos else None
            if ph:
                img, iw, ih = ph
                w = IMG_X1 - IMG_X0
                h = w * ih / iw
                if h > IMG_MAX_H:
                    h, w = IMG_MAX_H, IMG_MAX_H * iw / ih
                c.drawImage(img, IMG_X0 + (IMG_X1 - IMG_X0 - w) / 2, H - mid - h / 2, w, h)
            else:
                missing.append(r["CODE"])
            text(c, 140, mid - 3.7, r["CODE"], "AB", 8.5)
            if r["CODE"] in dots:
                c.setFillColorRGB(*DOT)
                c.circle(175, H - mid + 0.5, 3.6, stroke=0, fill=1)
                c.linkAbsolute("", "p1", (170, H - mid - 4.5, 180, H - mid + 5.5))
            text(c, 186, mid - 3.7, r["NAME"], "AR", 8.5)
            text(c, 464, mid - 3.7, r["UNIT"], "AR", 8.5)
            text(c, 562, mid - 4.1, price_text(r["PRICE"]), "AB", 9, align="r")
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.setLineWidth(0.5)
            c.line(L, H - top - ROW_H, R, H - top - ROW_H)
        if n == 1:
            c.bookmarkPage("p1")
            c.addOutlineEntry(section, "p1", 0)
        c.showPage()
    c.save()
    return len(chunks), missing


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--fincode")
    a.add_argument("--date", help="YYYY-MM-DD")
    a.add_argument("--csv")
    a.add_argument("--section", help="π.χ. «02. ΜΑΧΑΙΡΙΑ DICK ΓΕΡΜΑΝΙΑΣ» (αλλιώς το σχόλιο του παραστατικού)")
    a.add_argument("--title", default="ΤΙΜΟΚΑΤΑΛΟΓΟΣ ΧΟΝΔΡΙΚΗΣ 2027")
    a.add_argument("--photos")
    a.add_argument("--dots", default="", help="κωδικοί με κόκκινη βούλα, χωρισμένοι με κόμμα")
    a.add_argument("--out", required=True)
    o = a.parse_args()
    if o.csv:
        comments, rows = None, load_csv(o.csv)
    else:
        comments, rows = load_sql(o.fincode, o.date)
        with open(Path(o.out).with_suffix(".csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, ["CODE", "NAME", "UNIT", "PRICE"], delimiter=";")
            w.writeheader()
            w.writerows(rows)
    section = o.section or (comments or "").replace(".", ". ", 1)
    dots = {d.strip() for d in o.dots.split(",") if d.strip()}
    pages, missing = build(rows, o.out, o.title, section, o.photos, dots)
    codes = [r["CODE"] for r in rows]
    print(f"ΕΙΔΗ={len(rows)} ΣΕΛΙΔΕΣ={pages} ΔΙΠΛΟΙ={len(codes) - len(set(codes))} ΧΩΡΙΣ_ΦΩΤΟ={missing}")


if __name__ == "__main__":
    main()
