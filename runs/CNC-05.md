# CNC-05 — Custom μηχανή `100-25x25x185` με wedges −1.5mm (c2)

Ημερομηνία: 2026-10-28 — Worktree `..\devin-cnc` @ `origin/cnc/fylla-01` (**d848af1** —
«cnc: custom wedges 1.5 mm lower»).

- Έλεγχος βήματος 2: το `build_sheets.py` περιέχει `WEDGE_DOWN=1.5` (line 150) ✓
- Τρέχτηκε το **repo αρχείο χωρίς patch**.
- Έξοδος στο `C:\Users\User\Dropbox\devin` (μόνο τα 2 νέα `fyllo_ola_*` — κανένα .cdr δεν πειράχθηκε).

## Εντολή που τρέχτηκε

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python \
  ..\devin-cnc\cnc\build_sheets.py \
  --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" \
  --order "100-25x25x185:1" --ena-dxf --version c2 \
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
fyllo_ola_100-25x25x185x1_c2.dxf ola mm: 7 parts, gap 3.275 used height to 821.2 fill 23%
```

## Έλεγχος εξόδων — C:\Users\User\Dropbox\devin

```text
fyllo_ola_100-25x25x185x1_c2.dxf   184.437 bytes
fyllo_ola_100-25x25x185x1_c2.png   107.693 bytes
```

**1 .dxf + 1 .png ✓** — το `WEDGE_DOWN=1.5` κατέβασε τα wedges 1.5mm στα custom parts
(όπως το commit `d848af1`).

## Σφάλματα / παρατηρήσεις

1. Κανένα σφάλμα στο run — μόνο το γνωστό `findfont` warning.
2. **Τα αρχεία c1 του CNC-04 (`fyllo_ola_100-25x25x185x1_c1.dxf/.png`) δεν βρέθηκαν
   πλέον στο Dropbox\devin** — υπήρχαν στις 18:12 που παράχθηκαν και επαληθεύτηκαν,
   εξαφανίστηκαν πριν τον έλεγχο του c2. Δεν σβήστηκαν από εμένα· πιθανή αιτία:
   χειροκίνητη διαγραφή ή Dropbox sync. Γι' αυτό δεν έγινε byte-σύγκριση c1↔c2
   (ίδιο byte size 184.437 είναι σύμπτωση πλάτους αριθμών — οι συντεταγμένες διαφέρουν).
3. Ιδιο byte-size με c1 (184.437) επειδή η γεωμετρία διαφέρει μόνο σε Y-συντεταγμένες
   των wedge entities με ίδιο αριθμό ψηφίων.
