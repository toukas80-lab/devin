# SoftOne PDF Pilot

Τοπική Windows εφαρμογή για το pilot:

```text
PDF -> έλεγχος στοιχείων -> read-only SQL lookup -> dry-run
    -> SoftOne desktop UI Automation -> επιβεβαίωση αποθήκευσης
```

Η εφαρμογή:

- υποστηρίζει αρχικά **ENARTIA** και **ΕΓΝΑΤΙΑ ΟΔΟΣ**,
- χρησιμοποιεί τη SQL αποκλειστικά για `SELECT`,
- δεν παράγει XXF,
- δεν κάνει direct SQL `INSERT/UPDATE/DELETE`,
- ξεκινά πάντα σε dry-run,
- δεν αποθηκεύει κωδικούς SoftOne ή SQL.

## Τρέχουσα κατάσταση

Ο πυρήνας parsing, validation, read-only SQL lookup, duplicate check, batch preview και
control-tree inspection είναι διαθέσιμος. Η πραγματική συμπλήρωση της φόρμας SoftOne
θα ενεργοποιηθεί αφού καταγραφούν τα ακριβή controls της χειροκίνητης ροής.

## Εγκατάσταση για ανάπτυξη

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy config\local.example.json config\local.json
```

Το `config/local.json` μένει μόνο στον τοπικό υπολογιστή και δεν γίνεται commit.

## Χρήση

Ανάλυση ενός PDF:

```powershell
softone-pilot parse "C:\Invoices\invoice.pdf"
```

Dry-run φακέλου χωρίς SQL:

```powershell
softone-pilot dry-run "C:\Invoices" --no-sql
```

Κάθε dry-run γράφει συνοπτικό audit event στο `pilot-data/audit.jsonl`, χωρίς το
πλήρες κείμενο των PDF. Απενεργοποιείται προσωρινά με `--no-audit`.

Dry-run με read-only SQL:

```powershell
softone-pilot dry-run "C:\Invoices" --config config\local.json
```

Γραφικό περιβάλλον:

```powershell
softone-pilot-gui
```

Καταγραφή του UI Automation control tree του ήδη ανοικτού SoftOne:

```powershell
softone-pilot inspect-softone --workflow config\softone_workflow.example.json
```

Η παραπάνω εντολή δεν κάνει click και δεν αλλάζει δεδομένα.

Χωρίς εγκατάσταση Python, άνοιξε τη φόρμα-στόχο στο SoftOne και εκτέλεσε:

```text
scripts\run_softone_inspector.cmd
```

Δημιουργεί μόνο το `softone_controls.txt` στην Επιφάνεια Εργασίας. Δεν διαβάζει
κωδικούς και δεν κάνει καμία καταχώριση.

## Παραμετρικά workflows SoftOne

Το `config/softone_workflow.example.json` περιέχει ανεξάρτητα profiles για:

- `creditor_expense.create`: νέα εγγραφή στα Ειδικά πιστωτών.
- `creditor_expense.edit`: αλλαγή ήδη ανοικτού παραστατικού.

Τα πεδία εντοπίζονται από UI Automation labels και σχετικές θέσεις, όχι από
σταθερές συντεταγμένες. Νέοι τύποι παραστατικών προστίθενται ως νέο profile
χωρίς αλλαγή στον PDF parser.

Preview της ροής χωρίς άνοιγμα ή αλλαγή του SoftOne:

```powershell
softone-pilot workflow invoice.pdf `
  --config config\local.json `
  --profile creditor_expense.create
```

Το `--execute` συμπληρώνει την ήδη ανοικτή σωστή φόρμα, αλλά σταματά πριν την
αποθήκευση. Η αποθήκευση απαιτεί επιπλέον `--allow-save` και χρησιμοποιείται
μόνο μετά από ρητή έγκριση.

## Windows build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Το executable δημιουργείται στον φάκελο `dist`.

## Ασφάλεια

- Η σύνδεση SQL χρησιμοποιεί Windows authentication και `ApplicationIntent=ReadOnly`.
- Οι SQL εντολές του pilot είναι σταθερά, parameterized `SELECT`.
- Τα audit logs δεν περιέχουν κωδικούς ή το πλήρες περιεχόμενο των PDF.
- Η αυτοματοποίηση απορρίπτει πραγματική αποθήκευση μέχρι να υπάρχει ολοκληρωμένο,
  επιβεβαιωμένο workflow profile.
- Πριν από πραγματική καταχώριση απαιτείται νέα ρητή έγκριση και δοκιμή ενός παραστατικού.
