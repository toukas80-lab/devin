# CNC-18 — Φύλλο άνω πλάκες 00019 + custom 22.22 → t6

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `a1e1624`
(`cnc: ΤΕΜ=φύλλο fills a whole sheet with that part; fill tries 0°/90°
preference and keeps the better`, origin/cnc/fylla-01).
Check `def fill_try`: **βρέθηκε** (build_sheets.py line 311).
cdr-dir: `Dropbox\devin\ΠΡΟΤΥΠΑ` — out στο `Dropbox\devin`.
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή Α: φύλλο με άνω πλάκες 00019

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --order "00019:φύλλο:άνω" --version t6 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x2, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00019', 0, 'ano')]
00019 κομμάτια CDR: top 269.7x239.7, bottom 269.7x239.7, panel 255.0x245.0, panel 285.0x245.0
fill 25 mm: 28 κομμάτια σε 1 φύλλα
fyllo_25mm_00019xfyllo-ano_t6.dxf 25 mm: 28 parts, gap 3.275 used height to 1918.5 fill 88%
```

## Βήμα 4 — Εντολή Β: custom 100-22.22x22.22x185 (τελείες)

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --order "100-22.22x22.22x185:1" --version t6 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x2, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('100-22.22x22.22x185', 1, 'kivotio+kato+vasi+ano')]
fyllo_15mm_100-22.22x22.22x185x1_xoris-exolkea_t6.dxf 15 mm: 4 parts, gap 2.6 used height to 248.2 fill 11%
fyllo_20mm_100-22.22x22.22x185x1_xoris-exolkea_t6.dxf 20 mm: 2 parts, gap 3.275 used height to 272.2 fill 6%
fyllo_25mm_100-22.22x22.22x185x1_xoris-exolkea_t6.dxf 25 mm: 1 parts, gap 3.275 used height to 232.9 fill 2%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα** και στις δύο εντολές.

## Βήμα 5 — Παραγόμενα fyllo_*_t6 στο Dropbox\devin

| Αρχείο | Bytes | LastWriteTime |
|---|---|---|
| fyllo_25mm_00019xfyllo-ano_t6.dxf | 1.215.964 | 20:27:46 |
| fyllo_25mm_00019xfyllo-ano_t6.png | 646.371 | 20:27:47 |
| fyllo_15mm_100-22.22x22.22x185x1_xoris-exolkea_t6.dxf | 111.219 | 20:28:05 |
| fyllo_15mm_100-22.22x22.22x185x1_xoris-exolkea_t6.png | 48.110 | 20:28:06 |
| fyllo_20mm_100-22.22x22.22x185x1_xoris-exolkea_t6.dxf | 43.155 | 20:28:06 |
| fyllo_20mm_100-22.22x22.22x185x1_xoris-exolkea_t6.png | 60.784 | 20:28:06 |
| fyllo_25mm_100-22.22x22.22x185x1_xoris-exolkea_t6.dxf | 62.391 | 20:28:06 |
| fyllo_25mm_100-22.22x22.22x185x1_xoris-exolkea_t6.png | 62.264 | 20:28:06 |

**8 αρχεία** (4 φύλλα × dxf+png) — 1 από την εντολή Α + 3 από τη Β.

## Παρατηρήσεις

- **`ΤΕΜ=φύλλο`**: η `00019:φύλλο:άνω` γέμισε ΕΝΑ 25mm φύλλο με **28 άνω
  πλάκες** 269.7×239.7 (grid 4×7, 88%, ύψος 1918.5) — μόνο το part `άνω`,
  τίποτα άλλο. Το part πήγε στο 25mm sheet (πάχος πλάκας).
- **Custom με τελείες**: `100-22.22x22.22x185` έπαιξε κανονικά — 15mm:
  4 κομμάτια (11%), 20mm: 2 (6%), 25mm: 1 (2%), default `xoris-exolkea`.
- Order εμφανίζει `('00019', 0, 'ano')` — το qty 0 = σήμα «φύλλο» εσωτερικά.
- Οπτικός έλεγχος 25mm PNG: 28 πλάκες με hole-grids + labels — σωστό.
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε.
