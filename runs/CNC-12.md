# CNC-12 — Όλη η βιβλιοθήκη → v9 (16 μηχανές, χωρίς εξωλκέα)

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `49b85a8`
(`cnc: bases default without extractor hole; --exolkeas ναι adds Ø90/Ø66`,
origin/cnc/fylla-01).
Check `default='όχι'`: **βρέθηκε** (build_sheets.py line 15 — το `--exolkeas`
δεν δόθηκε → προεπιλογή «όχι», βάσεις χωρίς κύκλους Ø90/Ø66).
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" --version v9 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
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
fyllo_15mm_16mixanes_xoris-exolkea_f1of2_v9.dxf 15 mm: 33 parts, gap 2.6 used height to 1839.2 fill 81%
fyllo_15mm_16mixanes_xoris-exolkea_f2of2_v9.dxf 15 mm: 31 parts, gap 2.6 used height to 1442.5 fill 60%
fyllo_20mm_16mixanes_xoris-exolkea_v9.dxf 20 mm: 32 parts, gap 3.275 used height to 1779.4 fill 68%
fyllo_25mm_16mixanes_xoris-exolkea_v9.dxf 25 mm: 16 parts, gap 3.275 used height to 793.2 fill 28%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα** — και οι 16 μηχανές.

## Βήμα 4 — Παραγόμενα fyllo_*_v9 στο Dropbox\devin

| Αρχείο | Bytes | LastWriteTime |
|---|---|---|
| fyllo_15mm_16mixanes_xoris-exolkea_f1of2_v9.dxf | 2.012.234 | 19:47:08 |
| fyllo_15mm_16mixanes_xoris-exolkea_f1of2_v9.png | 163.676 | 19:47:09 |
| fyllo_15mm_16mixanes_xoris-exolkea_f2of2_v9.dxf | 1.530.301 | 19:47:09 |
| fyllo_15mm_16mixanes_xoris-exolkea_f2of2_v9.png | 134.316 | 19:47:10 |
| fyllo_20mm_16mixanes_xoris-exolkea_v9.dxf | 389.117 | 19:47:11 |
| fyllo_20mm_16mixanes_xoris-exolkea_v9.png | 282.480 | 19:47:11 |
| fyllo_25mm_16mixanes_xoris-exolkea_v9.dxf | 576.283 | 19:47:13 |
| fyllo_25mm_16mixanes_xoris-exolkea_v9.png | 277.013 | 19:47:13 |

**8 αρχεία** (4 φύλλα × dxf+png).

## Παρατηρήσεις

- **Πλήρης επιτυχία:** 16/16 μηχανές (είχαν 5 skips στο CNC-09/v8) — fixes:
  multi-page CDR read (00021) + marks-heuristic για top/bottom διαχωρισμό
  (00009, 00010, 00019, 00638).
- Τα ονόματα έχουν πλέον `xoris-exolkea` στο filename — εξαιτίας του
  `--exolkeas` default «όχι» (βάσεις χωρίς κύκλους Ø90/Ø66 στο κέντρο).
- 15mm: χωρίστηκε σε **2 φύλλα** (f1: 33 κομμάτια 81%, f2: 31 κομμάτια 60%)
  — σύνολο 64 κομμάτια vs 44 στο v8.
- 20mm: 32 κομμάτια (68%), 25mm: 16 κομμάτια (28%).
- Οπτικός έλεγχος 25mm PNG: πλάκες με grids + marks, χωρίς κεντρικούς
  κύκλους εξωλκέα — συνεπές με `xoris-exolkea`.
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε.
