# cnc 2026-10-31 1046 (KENTRIKO-SPITI) — ξανατρέξιμο τελευταίας εντολής με d8466dc (letters στο NC)

## Αίτημα
«Ξανατρέξε ΑΠΟ ΤΗΝ ΑΡΧΗ την τελευταία εντολή cnc με το ίδιο home Z· το NC πρέπει να γράφει letters.»
→ όλη η αλυσίδα του 1410 από το μηδέν: `00037:9` κομπλέ χωρίς γέμισμα → στήλες 2,3,4
+20 mm στο Y → `build_nc` με home Z 128.25. Νέα έκδοση `d8466dc` (XARAXI χάραξη στο ίδιο NC).

## Εντολές
```
git -C ..\devin-cnc checkout --detach origin/cnc/fylla-01   # HEAD d8466dc ✓
PYTHONIOENCODING=utf-8 uv run --no-project --with ezdxf --with svgpathtools --with matplotlib --with shapely python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --order "00037:9" --version 1046 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
uv run --no-project --with ezdxf python C:\Users\User\cnc_shift_y.py "...\fyllo_15mm_00037x9_xoris-exolkea_1046.dxf" "...\fyllo_15mm_00037x9_xoris-exolkea_1046_y+20.dxf"
uv run --no-project --with ezdxf --with shapely python ..\devin-cnc\cnc\build_nc.py --dxf "C:\Users\User\Dropbox\devin\2026-10-31\fyllo_15mm_00037x9_xoris-exolkea_1046_y+20.dxf" --home-z 128.25
```
Commit script κατά το run: `d8466dc` (origin/cnc/fylla-01).

## Έξοδος build_sheets
```
version d8466dc
order: [('00037', 9, 'kivotio+kato+vasi+ano')]
00037 κομμάτια CDR: panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
fyllo_15mm_00037x9_xoris-exolkea_1046.dxf 15 mm: 36 parts, gap 2.6 used height to 1966.8 material used 93%
fyllo_20mm_00037x9_xoris-exolkea_1046.dxf 20 mm: 18 parts, gap 3.275 used height to 1061.9 material used 43%
fyllo_25mm_00037x9_xoris-exolkea_1046.dxf 25 mm: 9 parts, gap 3.275 used height to 616.6 material used 18%
```
(ίδια τοποθέτηση με το 1354 — ίδια parts/ύψη/%)

## Μετατόπιση +20 mm (script C:\Users\User\cnc_shift_y.py — ξαναγραμμένο, υπήρχε μόνο στο μαγαζί)
```
columns: 4
  col 1: x 11.0..256.0, 279 entities, y 11.0..1966.8
  col 2: x 258.6..503.6, 279 entities, y 11.0..1966.8  <-- move
  col 3: x 506.2..751.2, 279 entities, y 11.0..1966.8  <-- move
  col 4: x 753.8..998.8, 279 entities, y 11.0..1966.8  <-- move
moved: 837
after: col 1 y 11.0..1966.8 (αμετάβλητη), cols 2-4 y 31.0..1986.8 (ακριβώς +20)
```
279 entities/στήλη πριν = 279 μετά (μαζί και τα XARAXI), κανένα χαμένο.

## Έξοδος build_nc — η γραμμές που ζητήθηκαν
```
version d8466dc
stages: 12 parts | 12 parts | 12 parts | 0 parts (boxes 9, 3 per stage)
NC C:\Users\User\Dropbox\devin\2026-10-31\fyllo_15mm_00037x9_xoris-exolkea_1046_y+20.nc lines 197519 | slits 216 wedges 216 cb Ø7+Ø3 108 holes 36 slots 0 pockets 0 pocket-circles 0 outlines 36 taps 0 letters 324 | home Z 128.250
```
Καμία ΠΡΟΣΟΧΗ.

## Έλεγχος NC
- `N40G43Z128.250H1M8` στην αρχή, παρκάρισμα `G00Z128.250` + `M30` στο τέλος ✓
- 324 blocks F2000 (χάραξη γραμμάτων), πρώτο στο N80 — πρώτα σε κάθε στάδιο, βάθη Z−0.001…−0.013 ✓
- `letters 324` στη γραμμή NC ✓

## Αποτέλεσμα
- `Dropbox\devin\2026-10-31\`: `fyllo_{15,20,25}mm_00037x9_xoris-exolkea_1046.dxf/.png`,
  `fyllo_15mm_..._1046_y+20.dxf/.png/.nc` (197.519 γραμμές, letters 324, home Z 128.250)
- Κανένα .cdr/άλλο αρχείο δεν πειράχθηκε.
