# cnc 2026-10-31 1524 (KENTRIKO-SPITI) — CNC-27: re-run 00037x9 +20mm @ 20cac0d, φύλλο 1015x2020, ασφάλεια 0

## Αίτημα
TASK CNC-27: fetch+detach σε `origin/cnc/fylla-01` (= `20cac0d` ✓ — νέο:
`--fyllo ΠΛxΜΗΚ` υποχρεωτικό και στα δύο προγράμματα· τα κλαμπ ακολουθούν το
πλάτος φύλλου). Ξανατρέχει ΑΠΟ ΤΗΝ ΑΡΧΗ την τελευταία εντολή cnc με το ίδιο
home Z (128.25), φύλλο 1015x2020, ασφάλεια 0.

## Εντολές
```
git -C ..\devin-cnc checkout --detach origin/cnc/fylla-01   # HEAD 20cac0d ✓
PYTHONIOENCODING=utf-8 uv run --no-project --with ezdxf --with svgpathtools --with matplotlib --with shapely python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --order "00037:9" --fyllo 1015x2020 --asfaleia 0 --version 1524 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
uv run --no-project --with ezdxf python C:\Users\User\cnc_shift_y.py "...\2026-10-31\fyllo_15mm_00037x9_xoris-exolkea_1524.dxf" "...\fyllo_15mm_00037x9_xoris-exolkea_1524_y+20.dxf"
uv run --no-project --with ezdxf --with shapely python ..\devin-cnc\cnc\build_nc.py --dxf "C:\Users\User\Dropbox\devin\2026-10-31\fyllo_15mm_00037x9_xoris-exolkea_1524_y+20.dxf" --fyllo 1015x2020 --home-z 128.25
```
Commit script κατά το run: `20cac0d` (origin/cnc/fylla-01).

## Έξοδος build_sheets (πλήρης)
```
version 20cac0d
order: [('00037', 9, 'kivotio+kato+vasi+ano')]
00037 κομμάτια CDR: panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
φύλλο 1015x2020, ασφάλεια 0 mm
fyllo_15mm_00037x9_xoris-exolkea_1524.dxf 15 mm: 36 parts, gap 2.6 used height to 1955.8 material used 93%
fyllo_20mm_00037x9_xoris-exolkea_1524.dxf 20 mm: 18 parts, gap 3.275 used height to 1011.6 material used 43%
fyllo_25mm_00037x9_xoris-exolkea_1524.dxf 25 mm: 9 parts, gap 3.275 used height to 402.7 material used 18%
```
Καμία ΠΡΟΣΟΧΗ. Ίδια τοποθέτηση με το run 1201 (ίδια parts/ύψη/%).

## Μετατόπιση +20 mm (στήλες 2,3,4 — script C:\Users\User\cnc_shift_y.py)
```
columns: 4
  col 1: x 0.0..245.0, 279 entities, y 0.0..1955.8
  col 2: x 247.6..492.6, 279 entities, y 0.0..1955.8  <-- move
  col 3: x 495.2..740.2, 279 entities, y 0.0..1955.8  <-- move
  col 4: x 742.8..987.8, 279 entities, y 0.0..1955.8  <-- move
moved: 837
after: col 1 y 0.0..1955.8 (αμετάβλητη), cols 2-4 y 20.0..1975.8 (ακριβώς +20)
```
279 entities/στήλη πριν = 279 μετά (μαζί και τα XARAXI).

## Έξοδος build_nc (πλήρης) — οι γραμμές που ζητήθηκαν
```
version 20cac0d
φύλλο 1015x2020
stages: 11 parts | 10 parts | 11 parts | 0 parts | 4 parts (boxes 9, 3 per stage)
κλαμπ: 4 κομμάτια (+0 τάπες) στο τέλος μετά από M00
NC C:\Users\User\Dropbox\devin\2026-10-31\fyllo_15mm_00037x9_xoris-exolkea_1524_y+20.nc lines 197500 | slits 216 wedges 216 cb Ø7+Ø3 108 holes 36 slots 0 pockets 0 pocket-circles 0 outlines 36 taps 0 letters 324 | home Z 128.250
```
Καμία ΠΡΟΣΟΧΗ. Ίδιο αποτέλεσμα με το run 1201 (στάδια `11|10|11|0|4`, κλαμπ 4, letters 324, 197.500 γραμμές).

## Έλεγχος NC
- `N40G43Z128.250H1M8` στην αρχή, παρκάρισμα `G00Z128.250` + `M30` στο τέλος ✓
- Στάση κλαμπ στο N1755110-5130: `G00Z128.250` → `M05` → `M00` (μετά `S15000M03` και κοπή των 4 κομματιών της ζώνης) ✓
- PNG ελέγχου `..._y+20.png` στον ίδιο φάκελο.

## Αποτέλεσμα
- `Dropbox\devin\2026-10-31\`: `fyllo_{15,20,25}mm_00037x9_xoris-exolkea_1524.dxf/.png`,
  `fyllo_15mm_..._1524_y+20.dxf/.png/.nc` (197.500 γραμμές, letters 324, κλαμπ 4, home Z 128.250)
- Κανένα .cdr/άλλο αρχείο δεν πειράχθηκε.
