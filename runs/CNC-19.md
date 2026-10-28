# CNC-19 — Φύλλο πλαϊνών 00034 + fill βίδες 00064 → t7 (dated subfolder)

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `937890a`
(`cnc: outputs go to a dated subfolder of --out-dir (YYYY-MM-DD)`,
origin/cnc/fylla-01).
Check `datetime.date.today`: **βρέθηκε** (build_sheets.py line 160 —
κάθε run γράφει σε `--out-dir\YYYY-MM-DD`).
cdr-dir: `Dropbox\devin\ΠΡΟΤΥΠΑ` — out στο `Dropbox\devin\2026-10-28`.
Repo script ΧΩΡΙΣ patch, με `PYTHONIOENCODING=utf-8`.

## Βήμα 3 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin\ΠΡΟΤΥΠΑ" --out-dir "C:\Users\User\Dropbox\devin" --order "00034:φύλλο:κιβώτιο" --fill "00064:15" --version t7 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
findfont: Font family 'Liberation Sans' not found.  (x1, DejaVu fallback)
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00034', 0, 'kivotio')]
00034 κομμάτια CDR: top 199.7x199.7, bottom 199.7x199.7, panel 215.0x245.0
fill 00064 00064.cdr 15 mm, κομμάτια: 45.0x41.1
fill 15 mm: 116 κομμάτια σε 1 φύλλα
fyllo_15mm_00034xfyllo-kivotio_t7.dxf 15 mm: 116 parts, gap 2.6 used height to 2007.6 fill 90%
```

**Καμία γραμμή `ΠΡΟΣΟΧΗ`, κανένα σφάλμα.**

## Βήμα 4 — Παραγόμενα στο Dropbox\devin\2026-10-28

| Αρχείο | Bytes | LastWriteTime |
|---|---|---|
| fyllo_15mm_00034xfyllo-kivotio_t7.dxf | 2.867.602 | 22:46:14 |
| fyllo_15mm_00034xfyllo-kivotio_t7.png | 292.086 | 22:46:15 |

**2 αρχεία** (1 φύλλο × dxf+png) — ο φάκελος `2026-10-28` δημιουργήθηκε
αυτόματα από το νέο dated-subfolder feature.

## Παρατηρήσεις

- `00034:φύλλο:κιβώτιο` → **32 panels** 215×245 (rotated, 8 σειρές × 4)
  γέμισαν το 15mm φύλλο.
- `fill "00064:15"` → νέο CDR `00064.cdr`, κομμάτι **45.0×41.1** (βίδα):
  **84 τμήματα** στοιβάχτηκαν στη δεξιά στενή ζώνη (~85mm) → σύνολο
  **116 κομμάτια, 90% fill**, ύψος 2007.6.
- Μόνο το part `κιβώτιο` ζητήθηκε — top/bottom της 00034 αγνοήθηκαν.
- Οπτικός έλεγχος PNG: panels rotated με κάθετα slots + στήλη βιδών —
  σωστό.
- Κανένα .cdr ή άλλο αρχείο στο Dropbox\devin δεν πειράχθηκε/σβήστηκε —
  μόνο ο νέος dated φάκελος με τα 2 αρχεία.
