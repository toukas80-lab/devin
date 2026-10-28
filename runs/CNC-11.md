# CNC-11 — Έλεγχος αναγνώρισης: 5 παραλειπόμενες με εξαναγκασμένο order

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `ba2e036`
(`cnc: read every CDR page (00021 has plates on page 1, panel on page 2)`,
origin/cnc/fylla-01).
Check `'bottom','top'`: **βρέθηκε** (build_sheets.py line 135 —
σε 2 ομοειδείς πλάκες, εκείνη με περισσότερα marks → top).
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.
Out-dir `%TEMP%\cnc11` — τίποτα στο Dropbox\devin.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "$env:TEMP\cnc11" --order "00009:1:κιβώτιο+άνω+κάτω,00010:1:κιβώτιο+άνω+κάτω,00019:1:κιβώτιο+άνω+κάτω,00021:1:κιβώτιο+άνω+κάτω,00638:1:κιβώτιο+άνω+κάτω" --ena-dxf --version k11 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x3, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00009', 1, 'kivotio+ano+kato'), ('00010', 1, 'kivotio+ano+kato'), ('00019', 1, 'kivotio+ano+kato'), ('00021', 1, 'kivotio+ano+kato'), ('00638', 1, 'kivotio+ano+kato')]
00009 κομμάτια CDR: panel 155.0x176.0, bottom 139.7x139.7, top 139.7x139.7
00010 κομμάτια CDR: top 209.7x209.7, bottom 209.7x209.7, panel 225.0x176.0
00019 κομμάτια CDR: top 269.7x239.7, bottom 269.7x239.7, panel 255.0x245.0, panel 285.0x245.0
00021 κομμάτια CDR: top 99.5x99.5, bottom 99.5x99.5, panel 115.0x210.0
00638 κομμάτια CDR: top 209.7x209.7, bottom 209.7x209.7, panel 225.0x176.0
fyllo_ola_00009x1-kivotio+ano+kato_00010x1-kivotio+ano+kato_00019x1-kivotio+ano+kato_00021x1-kivotio+ano+kato_00638x1-kivotio+ano+kato_k11.dxf ola mm: 30 parts, gap 3.275 used height to 1469.7 fill 56%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα.**

## Παραγόμενα στο %TEMP%\cnc11

| Αρχείο | Bytes |
|---|---|
| fyllo_ola_…_k11.dxf | 1.337.175 |
| fyllo_ola_…_k11.png | 271.559 |

## Αποτέλεσμα αναγνώρισης — ΚΑΙ ΟΙ 5 ΠΕΡΑΣΑΝ

| Μηχανή | parts στο CDR | Τι άλλαξε από CNC-09/10 |
|---|---|---|
| 00009 | panel + bottom + top 139.7² | Η marks-heuristic χώρισε τις 2 ίδιες πλάκες Ø7 → η πλάκα με τα ανοιχτά σημάδια έγινε top |
| 00010 | top + bottom 209.7² + panel | Αναγνωρίστηκε top (169× Ø5 vs 169× Ø8 / marks) |
| 00019 | top + bottom 269.7×239.7 + **2 panels** | Οι πλάκες Ø11 πια top/bottom, όχι panel |
| 00021 | top + bottom **99.5²** + panel | Οι πλάκες ήταν στη **σελίδα 1** του CDR — τώρα διαβάζονται όλες οι σελίδες |
| 00638 | top + bottom 209.7² + panel | Αναγνωρίστηκε top |

- Σύνολο: **30 κομμάτια** σε ένα DXF (`--ena-dxf`), 56% fill, ύψος 1469.7mm.
- Οπτικός έλεγχος PNG: σωστά nesting + labels 00021/00009/00638/00010/00019.
- Κανένα αρχείο στο Dropbox\devin δεν δημιουργήθηκε/πειράχθηκε — η δοκιμή
  έγραψε μόνο στο `%TEMP%\cnc11`.

**Συμπέρασμα:** οι 5 μηχανές είναι πλέον πλήρως επεξεργάσιμες στο `ba2e036` —
σε επόμενο library run θα συμμετάσχουν χωρίς ΠΡΟΣΟΧΗ.
