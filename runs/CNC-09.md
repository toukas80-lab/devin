# CNC-09 — Όλη η βιβλιοθήκη → v8 (skip αντί crash)

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `9863336`
(`cnc: top-plate detection ignores Ø7 holes; skip (not crash) machines with
unexpected CDR parts`, origin/cnc/fylla-01).
Check `skipped=[]`: **βρέθηκε** (build_sheets.py line 221).
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" --version v8 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x12, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00002', 1, 'kivotio+kato+vasi+ano'), ('00009', 1, 'kivotio+kato+vasi+ano'), ('00010', 1, 'kivotio+kato+vasi+ano'), ('00019', 1, 'kivotio+kato+vasi+ano'), ('00021', 1, 'kivotio+kato+vasi+ano'), ('00027', 1, 'kivotio+kato+vasi+ano'), ('00030', 1, 'kivotio+kato+vasi+ano'), ('00031', 1, 'kivotio+kato+vasi+ano'), ('00033', 1, 'kivotio+kato+vasi+ano'), ('00034', 1, 'kivotio+kato+vasi+ano'), ('00035', 1, 'kivotio+kato+vasi+ano'), ('00037', 1, 'kivotio+kato+vasi+ano'), ('00038', 1, 'kivotio+kato+vasi+ano'), ('00040', 1, 'kivotio+kato+vasi+ano'), ('00638', 1, 'kivotio+kato+vasi+ano'), ('00657', 1, 'kivotio+kato+vasi+ano')]
00002 κομμάτια CDR: panel 215.0x210.0, top 199.7x199.7, bottom 199.7x199.7
00009 κομμάτια CDR: panel 155.0x176.0, bottom 139.7x139.7, bottom 139.7x139.7
ΠΡΟΣΟΧΗ: 00009 παραλείπεται, το CDR δεν έχει 1 άνω + 1 κάτω + 1-2 πλαϊνά: ['panel', 'bottom', 'bottom']
00010 κομμάτια CDR: bottom 209.7x209.7, bottom 209.7x209.7, panel 225.0x176.0
ΠΡΟΣΟΧΗ: 00010 παραλείπεται, το CDR δεν έχει 1 άνω + 1 κάτω + 1-2 πλαϊνά: ['bottom', 'bottom', 'panel']
00019 κομμάτια CDR: panel 269.7x239.7, panel 269.7x239.7, panel 255.0x245.0, panel 285.0x245.0
ΠΡΟΣΟΧΗ: 00019 παραλείπεται, το CDR δεν έχει 1 άνω + 1 κάτω + 1-2 πλαϊνά: ['panel', 'panel', 'panel', 'panel']
00021 κομμάτια CDR: panel 115.0x210.0
ΠΡΟΣΟΧΗ: 00021 παραλείπεται, το CDR δεν έχει 1 άνω + 1 κάτω + 1-2 πλαϊνά: ['panel']
00027 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
00030 κομμάτια CDR: panel 215.0x245.0, panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
00031 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
00033 κομμάτια CDR: panel 215.0x245.0, panel 215.0x245.0, bottom 199.7x199.7, top 199.7x199.7
00034 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
00035 κομμάτια CDR: top 133.3x133.3, bottom 133.0x133.0, panel 148.3x245.0
00037 κομμάτια CDR: panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
00038 κομμάτια CDR: top 119.5x119.5, bottom 119.5x119.5, panel 135.0x210.0
00040 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0, panel 215.0x245.0
00638 κομμάτια CDR: bottom 209.7x209.7, bottom 209.7x209.7, panel 225.0x176.0
ΠΡΟΣΟΧΗ: 00638 παραλείπεται, το CDR δεν έχει 1 άνω + 1 κάτω + 1-2 πλαϊνά: ['bottom', 'bottom', 'panel']
00657 κομμάτια CDR: bottom 199.7x199.7, panel 215.0x210.0, top 199.7x199.7
fyllo_15mm_11mixanes_f1of2_v8.dxf 15 mm: 36 parts, gap 2.6 used height to 1966.8 fill 90%
fyllo_15mm_11mixanes_f2of2_v8.dxf 15 mm: 8 parts, gap 2.6 used height to 296.9 fill 13%
fyllo_20mm_11mixanes_v8.dxf 20 mm: 22 parts, gap 3.275 used height to 1263.3 fill 47%
fyllo_25mm_11mixanes_v8.dxf 25 mm: 11 parts, gap 3.275 used height to 616.6 fill 19%
```

## Βήμα 4 — Παραγόμενα fyllo_*_v8 στο Dropbox\devin

| Αρχείο | Bytes |
|---|---|
| fyllo_15mm_11mixanes_f1of2_v8.dxf | 2.021.351 |
| fyllo_15mm_11mixanes_f1of2_v8.png | 162.300 |
| fyllo_15mm_11mixanes_f2of2_v8.dxf | 560.648 |
| fyllo_15mm_11mixanes_f2of2_v8.png | 60.331 |
| fyllo_20mm_11mixanes_v8.dxf | 236.366 |
| fyllo_20mm_11mixanes_v8.png | 222.135 |
| fyllo_25mm_11mixanes_v8.dxf | 358.404 |
| fyllo_25mm_11mixanes_v8.png | 198.871 |

**8 αρχεία** (4 φύλλα × dxf+png). Οπτικός έλεγχος `f1of2` PNG: σωστό
dense nesting 36 panels με slots και κωδικούς.

## Παρατηρήσεις

- 16 μηχανές βρέθηκαν · **5 παραλείφθηκαν** με `ΠΡΟΣΟΧΗ` (όχι crash, όπως σχεδιάστηκε):
  - `00009` → panel + **2× bottom** (λείπει άνω)
  - `00010` → **2× bottom** + panel (λείπει άνω)
  - `00019` → **4× panel** (λείπουν άνω+κάτω)
  - `00021` → **μόνο 1 panel**
  - `00638` → **2× bottom** + panel (λείπει άνω)
- Η νέα top-plate detection (ignore Ø7 holes) αλλάζει την ταξινόμηση: στο CNC-08
  η 00009 εμφανιζόταν `top+top`, τώρα `bottom+bottom` — δηλ. τα CDR αυτά έχουν
  πιθανόν ξεχωριστά άνω/κάτω κομμάτια που δεν περιέχουν το grid οπών που
  περιμένει το script, ή λείπει όντως το «άνω».
- Η 00035 έχει μικρότερη πλάκα (133×133) και η 00038 ακόμα μικρότερη (119.5) —
  επεξεργάστηκαν κανονικά.
- To 15mm γέμισε ένα φύλλο στα 1966.8mm (90%) και ξεχείλισε σε **δεύτερο φύλλο**
  (`f1of2`/`f2of2`) — νέα συμπεριφορά αυτόματης σπασίματος.
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε.
