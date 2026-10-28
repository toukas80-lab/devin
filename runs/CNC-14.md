# CNC-14 — cdr-dir ΠΡΟΤΥΠΑ + join_open fix → t2

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `3c22cb5`
(`cnc: --fill joins open pieces that chain into one closed outline
(03923 = 175×17 with 2 slots)`, origin/cnc/fylla-01).
Check `def join_open`: **βρέθηκε** (build_sheets.py line 101).
cdr-dir: `Dropbox\devin\ΠΡΟΤΥΠΑ` (25 .cdr) — out στο `Dropbox\devin`.
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --order "00002:1::ναι,00009:1::ναι,00040:1::ναι,00030:1::ναι,00019:1::όχι" --fill "03923:15" --version t2 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x3, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00002', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00009', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00040', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00030', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00019', 1, 'kivotio+kato+vasi+ano', 'χωρίς εξωλκέα')]
00002 κομμάτια CDR: panel 215.0x210.0, top 199.7x199.7, bottom 199.7x199.7
00009 κομμάτια CDR: panel 155.0x176.0, bottom 139.7x139.7, top 139.7x139.7
00040 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0, panel 215.0x245.0
00030 κομμάτια CDR: panel 215.0x245.0, panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
00019 κομμάτια CDR: top 269.7x239.7, bottom 269.7x239.7, panel 255.0x245.0, panel 285.0x245.0
fill 03923 03923.cdr 15 mm, κομμάτια: 175.0x17.0
fill 15 mm: 231 × 1 κομμάτια
fyllo_15mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.dxf 15 mm: 251 parts, gap 2.6 used height to 2008.0 fill 81%
fyllo_20mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.dxf 20 mm: 10 parts, gap 3.275 used height to 735.2 fill 24%
fyllo_25mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.dxf 25 mm: 5 parts, gap 3.275 used height to 393.7 fill 10%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα.**

## Βήμα 4 — Παραγόμενα fyllo_*_t2 στο Dropbox\devin

| Αρχείο | Bytes | LastWriteTime |
|---|---|---|
| fyllo_15mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.dxf | 8.509.214 | 20:01:18 |
| fyllo_15mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.png | 370.923 | 20:01:19 |
| fyllo_20mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.dxf | 132.467 | 20:01:19 |
| fyllo_20mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.png | 133.022 | 20:01:19 |
| fyllo_25mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.dxf | 190.273 | 20:01:20 |
| fyllo_25mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t2.png | 123.929 | 20:01:20 |

**6 αρχεία** (3 φύλλα × dxf+png).

## Παρατηρήσεις

- **join_open fix:** το `03923.cdr` είναι στην πραγματικότητα **1 κομμάτι
  175.0×17.0** (λωρίδα με 2 slots) ζωγισμένο ως 4 ανοιχτά paths — στο CNC-13
  εμφανιζόταν λάθος ως «2× 35×17». Τώρα: **231 fill κομμάτια** (vs 601 ζεύγη).
- cdr-dir `ΠΡΟΤΥΠΑ` (υποφάκελος): 25 .cdr συνολικά, 16 αναγνωρίστηκαν ως
  μηχανές — τα υπόλοιπα είναι βοηθητικά (02536/02537/03839/03923 κ.λπ.).
- Οι 5 μηχανές όπως CNC-13 — ίδια order/per-machine εξωλκέα. Τα panels του
  order πήγαν κάτω, τα 231 strips γέμισαν τον υπόλοιπο χώρο μέχρι 2008mm (81%).
- Οπτικός έλεγχος 15mm PNG: σωστά closed strips 03923 με label ανά κομμάτι.
- 15mm dxf 8,5MB (vs 20,4MB στο t1 — λιγότερα, μεγαλύτερα κομμάτια).
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε.
