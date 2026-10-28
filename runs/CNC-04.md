# CNC-04 — Custom μηχανή `100-25x25x185` σε ένα DXF (c1)

Ημερομηνία: 2026-10-28 — Worktree `..\devin-cnc` @ `origin/cnc/fylla-01` (**c9b949a** —
«cnc: custom machines N-AxBxL in --order (+ --ena-dxf: all parts in one DXF)»).

- Έλεγχος βήματος 2: το `build_sheets.py` περιέχει `def custom_parts` (line 155) ✓
- Τρέχτηκε το **repo αρχείο χωρίς patch**.
- Έξοδος απευθείας στο `C:\Users\User\Dropbox\devin` (μόνο τα 2 νέα `fyllo_ola_*` αρχεία — κανένα .cdr δεν πειράχθηκε).

## Εντολή που τρέχτηκε

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python \
  ..\devin-cnc\cnc\build_sheets.py \
  --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" \
  --order "100-25x25x185:1" --ena-dxf --version c1 \
  --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

## Έξοδος (πλήρης)

```text
findfont: Font family 'Liberation Sans' not found.   (x2 — fallback σε DejaVu Sans)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('100-25x25x185', 1, 'kivotio+kato+vasi+ano')]
fyllo_ola_100-25x25x185x1_c1.dxf ola mm: 7 parts, gap 3.275 used height to 821.2 fill 23%
```

## Έλεγχος εξόδων — C:\Users\User\Dropbox\devin

```text
fyllo_ola_100-25x25x185x1_c1.dxf   184.437 bytes
fyllo_ola_100-25x25x185x1_c1.png   107.662 bytes
```

**1 .dxf + 1 .png ✓** — το `--order "100-25x25x185:1"` παρήγαγε custom μηχανή
(100 τρυπες / σουβλάκι 25×25×185, ×1 σετ) και το `--ena-dxf` έβαλε **όλα τα 7
τμήματα σε ένα DXF** (κιβώτιο+κάτω+βάση+άνω).
Οπτικός έλεγχος PNG: base 239×239 με κυκλικό άνοιγμα, κάτω/άνω πλάκες με grid
οπών-τριγώνων, 4 πλαϊνά με slots — nesting 1015×2020, used height 821.2, fill 23%.

## Σφάλματα

Κανένα — ολοκληρώθηκε χωρίς σφάλμα. Μόνο το γνωστό `findfont` warning
('Liberation Sans' δεν υπάρχει → DejaVu Sans fallback).
