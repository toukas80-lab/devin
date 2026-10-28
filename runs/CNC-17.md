# CNC-17 — 8 μηχανές με εξωλκέα + fill 03923:15 → t5

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `a4b5f87`
(`cnc: fill keeps gap from real part extents`, origin/cnc/fylla-01).
Check `def fill_sheet`: **βρέθηκε** (build_sheets.py line 307).
cdr-dir: `Dropbox\devin\ΠΡΟΤΥΠΑ` — out στο `Dropbox\devin`.
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --order "00002:1::ναι,00009:1::ναι,00010:1::ναι,00019:1::ναι,00021:1::ναι,00027:1::ναι,00030:1::ναι,00031:1::ναι" --fill "03923:15" --version t5 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x6, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00002', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00009', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00010', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00019', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00021', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00027', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00030', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00031', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας')]
00002 κομμάτια CDR: panel 215.0x210.0, top 199.7x199.7, bottom 199.7x199.7
00009 κομμάτια CDR: panel 155.0x176.0, bottom 139.7x139.7, top 139.7x139.7
00010 κομμάτια CDR: top 209.7x209.7, bottom 209.7x209.7, panel 225.0x176.0
00019 κομμάτια CDR: top 269.7x239.7, bottom 269.7x239.7, panel 255.0x245.0, panel 285.0x245.0
00021 κομμάτια CDR: top 99.5x99.5, bottom 99.5x99.5, panel 115.0x210.0
00027 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
00030 κομμάτια CDR: panel 215.0x245.0, panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
00031 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
fill 03923 03923.cdr 15 mm, κομμάτια: 175.0x17.0
fill 15 mm: 129 κομμάτια σε 1 φύλλα
fyllo_15mm_8kodikoi_00002-00009-00010-00019-00021-00027-00030-00031_t5.dxf 15 mm: 161 parts, gap 2.6 used height to 2002.4 fill 89%
fyllo_20mm_8kodikoi_00002-00009-00010-00019-00021-00027-00030-00031_t5.dxf 20 mm: 16 parts, gap 3.275 used height to 948.2 fill 35%
fyllo_25mm_8kodikoi_00002-00009-00010-00019-00021-00027-00030-00031_t5.dxf 25 mm: 8 parts, gap 3.275 used height to 453.7 fill 15%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα** — και οι 8 μηχανές με εξωλκέα.

## Βήμα 4 — Παραγόμενα fyllo_*_t5 στο Dropbox\devin

| Αρχείο | Bytes | LastWriteTime |
|---|---|---|
| fyllo_15mm_8kodikoi_00002-…-00031_t5.dxf | 6.000.477 | 20:21:04 |
| fyllo_15mm_8kodikoi_00002-…-00031_t5.png | 306.347 | 20:21:05 |
| fyllo_20mm_8kodikoi_00002-…-00031_t5.dxf | 213.432 | 20:21:05 |
| fyllo_20mm_8kodikoi_00002-…-00031_t5.png | 192.359 | 20:21:06 |
| fyllo_25mm_8kodikoi_00002-…-00031_t5.dxf | 315.934 | 20:21:06 |
| fyllo_25mm_8kodikoi_00002-…-00031_t5.png | 170.143 | 20:21:07 |

**6 αρχεία** (3 φύλλα × dxf+png). Νέο filename format `8kodikoi_<codes>`.

## Παρατηρήσεις

- 15mm: **161 κομμάτια, 89% fill** σε ΕΝΑ φύλλο (32 parts order +
  **129 strips 03923** σε κάθε κενό — πάνω ζώνη, δεξιά άκρη κάθετα,
  ανάμεσα στα panels). Χωράνε όλες οι 8 μηχανές σε ένα φύλλο.
- 20mm: 16 κομμάτια (35%), 25mm: 8 κομμάτια (15%) — χωρίς fill.
- Order δείχνει `εξωλκέας` και στις 8 — filenames `8kodikoi_…`.
- Οπτικός έλεγχος 15mm PNG: σωστό nesting, strips closed με labels.
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε.
