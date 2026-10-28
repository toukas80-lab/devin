# CNC-16 — Όλη η βιβλιοθήκη + εξωλκέας + fill σε κάθε κενό → t4

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `a4b5f87`
(`cnc: fill keeps gap from real part extents`, origin/cnc/fylla-01).
Check `def fill_sheet`: **βρέθηκε** (build_sheets.py line 307 — maxrects:
ρίχνει fill κομμάτια και στις δύο στροφές σε κάθε ελεύθερο κενό).
cdr-dir: `Dropbox\devin\ΠΡΟΤΥΠΑ` — out στο `Dropbox\devin`.
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --exolkeas ναι --fill "03839:20,03923:15" --version t4 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x12, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00002', 1, 'kivotio+kato+vasi+ano'), ('00009', 1, 'kivotio+kato+vasi+ano'), ('00010', 1, 'kivotio+kato+vasi+ano'), ('00019', 1, 'kivotio+kato+vasi+ano'), ('00021', 1, 'kivotio+kato+vasi+ano'), ('00027', 1, 'kivotio+kato+vasi+ano'), ('00030', 1, 'kivotio+kato+vasi+ano'), ('00031', 1, 'kivotio+kato+vasi+ano'), ('00033', 1, 'kivotio+kato+vasi+ano'), ('00034', 1, 'kivotio+kato+vasi+ano'), ('00035', 1, 'kivotio+kato+vasi+ano'), ('00037', 1, 'kivotio+kato+vasi+ano'), ('00038', 1, 'kivotio+kato+vasi+ano'), ('00040', 1, 'kivotio+kato+vasi+ano'), ('00638', 1, 'kivotio+kato+vasi+ano'), ('00657', 1, 'kivotio+kato+vasi+ano')]
00002 κομμάτια CDR: panel 215.0x210.0, top 199.7x199.7, bottom 199.7x199.7
00009 κομμάτια CDR: panel 155.0x176.0, bottom 139.7x139.7, top 139.7x139.7
00010 κομμάτια CDR: top 209.7x209.7, bottom 209.7x209.7, panel 225.0x176.0
00019 κομμάτια CDR: top 269.7x239.7, bottom 269.7x239.7, panel 255.0x245.0, panel 285.0x245.0
00021 κομμάτια CDR: top 99.5x99.5, bottom 99.5x99.5, panel 115.0x210.0
00027 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
00030 κομμάτια CDR: panel 215.0x245.0, panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
00031 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
00033 κομμάτια CDR: panel 215.0x245.0, panel 215.0x245.0, bottom 199.7x199.7, top 199.7x199.7
00034 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
00035 κομμάτια CDR: top 133.3x133.3, bottom 133.0x133.0, panel 148.3x245.0
00037 κομμάτια CDR: panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
00038 κομμάτια CDR: top 119.5x119.5, bottom 119.5x119.5, panel 135.0x210.0
00040 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0, panel 215.0x245.0
00638 κομμάτια CDR: top 209.7x209.7, bottom 209.7x209.7, panel 225.0x176.0
00657 κομμάτια CDR: bottom 199.7x199.7, panel 215.0x210.0, top 199.7x199.7
fill 03839 03839.cdr 20 mm, κομμάτια: 89.7x89.7
fill 03923 03923.cdr 15 mm, κομμάτια: 175.0x17.0
fill 20 mm: 33 κομμάτια σε 1 φύλλα
fill 15 mm: 257 κομμάτια σε 2 φύλλα
fyllo_15mm_16mixanes_exolkeas_f1of2_t4.dxf 15 mm: 99 parts, gap 2.6 used height to 1996.0 fill 90%
fyllo_15mm_16mixanes_exolkeas_f2of2_t4.dxf 15 mm: 222 parts, gap 2.6 used height to 2002.4 fill 87%
fyllo_20mm_16mixanes_exolkeas_t4.dxf 20 mm: 65 parts, gap 3.275 used height to 1980.9 fill 81%
fyllo_25mm_16mixanes_exolkeas_t4.dxf 25 mm: 16 parts, gap 3.275 used height to 793.2 fill 28%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα** — και οι 16 μηχανές.

## Βήμα 4 — Παραγόμενα fyllo_*_t4 στο Dropbox\devin

| Αρχείο | Bytes | LastWriteTime |
|---|---|---|
| fyllo_15mm_16mixanes_exolkeas_f1of2_t4.dxf | 4.216.125 | 20:14:14 |
| fyllo_15mm_16mixanes_exolkeas_f1of2_t4.png | 242.808 | 20:14:15 |
| fyllo_15mm_16mixanes_exolkeas_f2of2_t4.dxf | 7.920.456 | 20:14:17 |
| fyllo_15mm_16mixanes_exolkeas_f2of2_t4.png | 364.157 | 20:14:18 |
| fyllo_20mm_16mixanes_exolkeas_t4.dxf | 411.775 | 20:14:19 |
| fyllo_20mm_16mixanes_exolkeas_t4.png | 426.544 | 20:14:20 |
| fyllo_25mm_16mixanes_exolkeas_t4.dxf | 576.281 | 20:14:21 |
| fyllo_25mm_16mixanes_exolkeas_t4.png | 277.013 | 20:14:22 |

**8 αρχεία** (4 φύλλα × dxf+png).

## Παρατηρήσεις — το νέο fill γεμίζει ΚΑΘΕ φύλλο (όχι μόνο το τελευταίο)

| Φύλλο | t3 (πριν) | t4 (τώρα) |
|---|---|---|
| 15mm f1 | 33 κομμάτια, 81%, **0 strips** | 99 κομμάτια, **90%**, +66 strips 03923 |
| 15mm f2 | 173, 80% | 222, **87%**, +191 strips |
| 20mm | 55, 77% | 65, **81%**, +33 τμήματα 03839 |
| 25mm | 16, 28% | 16, 28% (χωρίς fill — δεν ζητήθηκε) |

- Σύνολο fill: **257 strips 03923** στα δύο 15mm φύλλα + **33 τμήματα 03839**
  στο 20mm (έναντι 142+23 στο t3 — ο maxrects γεμίζει και τα κενά ανάμεσα
  στα panels, όχι μόνο την κορυφή).
- Οπτικός έλεγχος f1: strips 03923 στην πάνω ζώνη, στην **δεξιά άκρη κάθετα**
  και σε κενά ανάμεσα στα panels — «keep gap from real part extents».
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε.
