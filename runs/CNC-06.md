# CNC-06 — Φύλλα v6 (7 μηχανές) + custom c3 με κεντραρισμένα τρίγωνα

Ημερομηνία: 2026-10-28 — Worktree `..\devin-cnc` @ `origin/cnc/fylla-01` (**902a0d5** —
«cnc: custom top-plate triangles centred on the new grid lines»).

- Έλεγχος βήματος 2: το `build_sheets.py` περιέχει `y+k*b-20` (line 193) ✓
- Τρέχτηκε το **repo αρχείο χωρίς patch** και στις δύο εντολές.
- Έξοδος στο `C:\Users\User\Dropbox\devin` (μόνο τα 8 νέα `fyllo_*` — κανένα .cdr δεν πειράχθηκε).

## Εντολή 3α (7 μηχανές, --version v6)

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python \
  ..\devin-cnc\cnc\build_sheets.py \
  --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" \
  --version v6 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

### Έξοδος 3α (πλήρης)

```text
findfont: Font family 'Liberation Sans' not found.   (x5 — fallback σε DejaVu Sans)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00002', 1, 'kivotio+kato+vasi+ano'), ('00030', 1, 'kivotio+kato+vasi+ano'),
 ('00031', 1, 'kivotio+kato+vasi+ano'), ('00033', 1, 'kivotio+kato+vasi+ano'),
 ('00034', 1, 'kivotio+kato+vasi+ano'), ('00040', 1, 'kivotio+kato+vasi+ano'),
 ('00657', 1, 'kivotio+kato+vasi+ano')]
fyllo_15mm_7mixanes_v6.dxf 15 mm: 28 parts, gap 2.6 used height to 1531.6 fill 69%
fyllo_20mm_7mixanes_v6.dxf 20 mm: 14 parts, gap 3.275 used height to 898.2 fill 33%
fyllo_25mm_7mixanes_v6.dxf 25 mm: 7 parts, gap 3.275 used height to 413.7 fill 14%
```

## Εντολή 3β (custom --ena-dxf, --version c3)

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python \
  ..\devin-cnc\cnc\build_sheets.py \
  --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" \
  --order "100-25x25x185:1" --ena-dxf --version c3 \
  --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

### Έξοδος 3β (πλήρης)

```text
findfont: Font family 'Liberation Sans' not found.   (x2)
machines: {ίδιο λεξικό 7 μηχανών όπως παραπάνω}
order: [('100-25x25x185', 1, 'kivotio+kato+vasi+ano')]
fyllo_ola_100-25x25x185x1_c3.dxf ola mm: 7 parts, gap 3.275 used height to 821.2 fill 23%
```

## Έλεγχος εξόδων — C:\Users\User\Dropbox\devin (8 αρχεία)

```text
fyllo_15mm_7mixanes_v6.dxf          1.441.658 bytes
fyllo_15mm_7mixanes_v6.png            129.787 bytes
fyllo_20mm_7mixanes_v6.dxf            167.018 bytes
fyllo_20mm_7mixanes_v6.png            168.852 bytes
fyllo_25mm_7mixanes_v6.dxf            247.433 bytes
fyllo_25mm_7mixanes_v6.png            149.625 bytes
fyllo_ola_100-25x25x185x1_c3.dxf      184.430 bytes
fyllo_ola_100-25x25x185x1_c3.png      107.493 bytes
```

**8/8 αρχεία ✓** — v6 (15/20/25mm ×7 μηχανές) + custom c3 (ένα DXF).
Διαφορά `902a0d5`: τα τρίγωνα της top-plate κεντραρίζονται στις νέες grid lines
(custom parts). Ίδιο nesting/fill με v5.

## Σφάλματα

Κανένα — και τα δύο runs ολοκληρώθηκαν χωρίς σφάλμα. Μόνο το γνωστό
`findfont` warning ('Liberation Sans' → DejaVu Sans fallback).
