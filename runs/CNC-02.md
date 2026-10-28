# CNC-02 — Φύλλα CNC 15/20/25 mm από CDR templates (v4)

Ημερομηνία: 2026-10-28 — Worktree `..\devin-cnc` @ `origin/cnc/fylla-01` (**f0221a5** —
«cnc: svg height from viewBox, fallback to height (both libcdr versions)»,
επίσης `df8e13f` «entity colour 250 like CorelDRAW DXF export»).

- Έλεγχος βήματος 2: το `build_sheets.py` περιέχει `'color':250` (line 51) ✓
- Τρέχτηκε το **repo αρχείο χωρίς patch** — η διόρθωση viewBox/height είναι πλέον στο branch.

## Εντολή που τρέχτηκε

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python \
  ..\devin-cnc\cnc\build_sheets.py \
  --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "%USERPROFILE%\Desktop\FYLLA_CNC" \
  --version v4 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

## Έξοδος (πλήρης)

```text
findfont: Font family 'Liberation Sans' not found.   (x5 — fallback σε DejaVu Sans)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr',
 '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
15 mm: 28 parts, gap 2.6 used height to 1531.6 fill 69%
20 mm: 14 parts, gap 3.275 used height to 898.2 fill 33%
25 mm: 7 parts, gap 3.275 used height to 413.7 fill 14%
```

## Έλεγχος εξόδων — Desktop\FYLLA_CNC (v4)

```text
fyllo_15mm_7mixanes_v4.dxf    1.459.369 bytes
fyllo_15mm_7mixanes_v4.png      130.024 bytes
fyllo_20mm_7mixanes_v4.dxf      170.170 bytes
fyllo_20mm_7mixanes_v4.png      169.043 bytes
fyllo_25mm_7mixanes_v4.dxf      249.046 bytes
fyllo_25mm_7mixanes_v4.png      149.940 bytes
```

**3 .dxf + 3 .png (15/20/25mm) ✓** — ίδιο nesting με v3 (28/14/7 κομμάτια, ίδια fill%).
Τα .dxf είναι ελαφρώς μεγαλύτερα από v3 (color attribute 250 ανά entity — όπως το
CorelDRAW DXF export). Τα .png είναι byte-identical με τα v3 (ίδιο layout).

## Σφάλματα

Κανένα — ολοκληρώθηκε χωρίς σφάλμα. Μόνο το γνωστό `findfont` warning
('Liberation Sans' δεν υπάρχει → DejaVu Sans fallback για τα text contours).
