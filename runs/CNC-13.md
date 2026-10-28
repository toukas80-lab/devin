# CNC-13 — 5 μηχανές με per-machine εξωλκέα + --fill 03923:15 → t1

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `c75612a`
(`cnc: per-machine extractor choice (CODE:QTY:PARTS:ναι/όχι) and --fill CODE:MM
to fill a sheet's free space`, origin/cnc/fylla-01).
Check `--fill`: **βρέθηκε** (build_sheets.py line 16).
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" --order "00002:1::ναι,00009:1::ναι,00040:1::ναι,00030:1::ναι,00019:1::όχι" --fill "03923:15" --version t1 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x3, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00002', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00009', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00040', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00030', 1, 'kivotio+kato+vasi+ano', 'εξωλκέας'), ('00019', 1, 'kivotio+kato+vasi+ano', 'χωρίς εξωλκέα')]
00002 κομμάτια CDR: panel 215.0x210.0, top 199.7x199.7, bottom 199.7x199.7
00009 κομμάτια CDR: panel 155.0x176.0, bottom 139.7x139.7, top 139.7x139.7
00040 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0, panel 215.0x245.0
00030 κομμάτια CDR: panel 215.0x245.0, panel 215.0x245.0, top 199.7x199.7, bottom 199.7x199.7
00019 κομμάτια CDR: top 269.7x239.7, bottom 269.7x239.7, panel 255.0x245.0, panel 285.0x245.0
fill 03923 03923.cdr 15 mm, κομμάτια: 35.0x17.0, 35.0x17.0
fill 15 mm: 601 × 2 κομμάτια
fyllo_15mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.dxf 15 mm: 1222 parts, gap 2.6 used height to 2008.0 fill 82%
fyllo_20mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.dxf 20 mm: 10 parts, gap 3.275 used height to 735.2 fill 24%
fyllo_25mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.dxf 25 mm: 5 parts, gap 3.275 used height to 393.7 fill 10%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα.**

## Βήμα 4 — Παραγόμενα fyllo_*_t1 στο Dropbox\devin

| Αρχείο | Bytes | LastWriteTime |
|---|---|---|
| fyllo_15mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.dxf | 20.373.310 | 19:55:58 |
| fyllo_15mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.png | 891.079 | 19:56:01 |
| fyllo_20mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.dxf | 132.469 | 19:56:01 |
| fyllo_20mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.png | 133.022 | 19:56:01 |
| fyllo_25mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.dxf | 190.274 | 19:56:02 |
| fyllo_25mm_00002x1-exo_00009x1-exo_00040x1-exo_00030x1-exo_00019x1-xoris_t1.png | 123.929 | 19:56:02 |

**6 αρχεία** (3 φύλλα × dxf+png).

## Παρατηρήσεις

- Per-machine εξωλκέας δούλεψε: order δείχνει `εξωλκέας` στις 4 πρώτες,
  `χωρίς εξωλκέα` στη 00019 — filenames με `-exo` / `-xoris`.
- **`--fill "03923:15"`**: το `03923.cdr` βρέθηκε by-prefix (νέο αρχείο,
  13.163B) — έχει 2 κομμάτια 35.0×17.0 → **601 ζεύγη (1.202 κομμάτια)**
  γέμισαν τον κενό χώρο του 15mm: σύνολο **1.222 κομμάτια, 82% fill**,
  used height 2008.0mm (σχεδόν πλήρες φύλλο).
- Το 15mm dxf είναι **20,4MB** λόγω των 1.222 κομματιών — πολύ πιο βαρύ
  από τα συνηθισμένα (~2MB).
- 20mm: 10 κομμάτια (24%), 25mm: 5 κομμάτια (10%) — χωρίς fill σε αυτά.
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε.
