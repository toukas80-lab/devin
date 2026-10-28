# CNC-08 — Όλη η βιβλιοθήκη → v7

Ημερομηνία: 2026-10-28 — worktree `..\devin-cnc` detached @ `b78d560`
(`cnc: read CDR library also from sub-folders`, origin/cnc/fylla-01).
Check `recursive=True`: **βρέθηκε** (build_sheets.py γραμμές 142, 148).

## Βήμα 3 — Λίστα .cdr στο Dropbox\devin (πλήρης έξοδος)

```powershell
Get-ChildItem "C:\Users\User\Dropbox\devin" -Recurse -Filter *.cdr | Select-Object @{n='Path';e={$_.FullName.Replace('C:\Users\User\Dropbox\devin\','')}}, Length, LastWriteTime | Format-Table -AutoSize | Out-String -Width 300
```

```text
Path                        Length LastWriteTime        
----                        ------ -------------        
00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr    42114 28/10/2026 2:03:17 μμ
00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr    48302 28/10/2026 6:38:05 μμ
00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr    54390 28/10/2026 6:42:53 μμ
00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr  1421399 28/10/2026 6:30:15 μμ
00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr  1395351 28/10/2026 6:40:36 μμ
00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr  1423744 28/10/2026 6:28:24 μμ
00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr  1414205 28/10/2026 2:08:52 μμ
00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr  1406359 28/10/2026 2:10:05 μμ
00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr  1410249 28/10/2026 2:20:55 μμ
00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr  1413780 28/10/2026 2:07:12 μμ
00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr  1405010 28/10/2026 6:32:57 μμ
00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr  1405191 28/10/2026 6:31:30 μμ
00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr  1394065 28/10/2026 6:36:35 μμ
00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr    37624 28/10/2026 2:05:51 μμ
00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr    72490 28/10/2026 6:45:25 μμ
00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr 1416668 28/10/2026 2:00:57 μμ
02536.cdr                    13047 28/10/2026 1:53:04 μμ
02537.cdr                    12412 28/10/2026 1:53:43 μμ
03839.cdr                    16776 28/10/2026 1:54:49 μμ
```

**19 .cdr** — 16 μηχανές `ΠΛΑΪΝΟ/ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ` + 3 σκέτα.

## Βήμα 4 — Εντολή και πλήρης έξοδος

```text
uv run --no-project --with ezdxf --with svgpathtools --with matplotlib python ..\devin-cnc\cnc\build_sheets.py --cdr-dir "C:\Users\User\Dropbox\devin" --out-dir "C:\Users\User\Dropbox\devin" --version v7 --cdr2xhtml "C:\msys64\ucrt64\bin\cdr2xhtml.exe"
```

```text
Installed 17 packages in 806ms
machines: {'00002': '00002 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00009': '00009 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00010': '00010 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00019': '00019 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00021': '00021 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00027': '00027 ΠΛΑΪΝO ΑΝΩ ΚΑΤΩ.cdr', '00030': '00030 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00031': '00031 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00033': '00033 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00034': '00034 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00035': '00035 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00037': '00037 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00038': '00038 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00040': '00040 ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr', '00638': '00638 ΠΛΑΪΝΟ ΑΝΩ ΚΑΤΩ.cdr', '00657': '00657  ΠΛΑΪΝΑ ΑΝΩ ΚΑΤΩ.cdr'}
order: [('00002', 1, 'kivotio+kato+vasi+ano'), ('00009', 1, 'kivotio+kato+vasi+ano'), ('00010', 1, 'kivotio+kato+vasi+ano'), ('00019', 1, 'kivotio+kato+vasi+ano'), ('00021', 1, 'kivotio+kato+vasi+ano'), ('00027', 1, 'kivotio+kato+vasi+ano'), ('00030', 1, 'kivotio+kato+vasi+ano'), ('00031', 1, 'kivotio+kato+vasi+ano'), ('00033', 1, 'kivotio+kato+vasi+ano'), ('00034', 1, 'kivotio+kato+vasi+ano'), ('00035', 1, 'kivotio+kato+vasi+ano'), ('00037', 1, 'kivotio+kato+vasi+ano'), ('00038', 1, 'kivotio+kato+vasi+ano'), ('00040', 1, 'kivotio+kato+vasi+ano'), ('00638', 1, 'kivotio+kato+vasi+ano'), ('00657', 1, 'kivotio+kato+vasi+ano')]
00002 κομμάτια CDR: panel 215.0x210.0, top 199.7x199.7, bottom 199.7x199.7
00009 κομμάτια CDR: panel 155.0x176.0, top 139.7x139.7, top 139.7x139.7
Traceback (most recent call last):
  File "C:\Users\User\Documents\devin-cnc\cnc\build_sheets.py", line 227, in <module>
    assert len(one('top'))==1 and len(one('bottom'))==1 and len(pan) in (1,2),(code,[p['kind'] for p in ps])
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('00009', ['panel', 'top', 'top'])
```

(Στο πραγματικό console τα ελληνικά ονόματα εμφανίστηκαν ως `????`· εδώ αποκαταστάθηκαν.)

**ΣΦΑΛΜΑ — AssertionError στο 00009:** το CDR της μηχανής 00009 περιέχει
`panel + top + top` (δύο «top» τμήματα, κανένα «bottom»). Το script απαιτεί
ακριβώς 1 top + 1 bottom + 1–2 panel (line 227) → κρασάρει πριν παράξει οτιδήποτε.
Δεν εκτυπώθηκε «ΠΡΟΣΟΧΗ». Repo script χωρίς patch — δεν άλλαξα τον κώδικα.

## Βήμα 5 — Παραγόμενα fyllo_*_v7 στο Dropbox\devin

```text
(κανένα αρχείο — το AssertionError σταμάτησε τη διαδικασία πριν την παραγωγή)
```

## Παρατηρήσεις

- Από τα CNC-01..06 προστέθηκαν 9 νέα .cdr:
  00009, 00010, 00019, 00021, 00027, 00035, 00037, 00038, 00638.
- Η 00009 έχει μη-τυπική δομή (2× top, 0× bottom) — πιθανόν λείπει/δεν
  αναγνωρίστηκε το «κάτω» τμήμα στο CDR, ή πρόκειται για μηχανή με
  διαφορετικό layout. Χρειάζεται είτε διόρθωση του CDR είτε χαλάρωση του
  assert / χειρισμό «top+top» περίπτωσης στο script.
- Κανένα .cdr ή άλλο αρχείο δεν πειράχθηκε/σβήστηκε.
