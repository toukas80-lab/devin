# SoftOne PDF Pilot

Τοπική Windows εφαρμογή για το pilot:

```text
PDF -> έλεγχος στοιχείων -> read-only SQL lookup -> dry-run
    -> SoftOne desktop UI Automation -> επιβεβαίωση αποθήκευσης
```

Η εφαρμογή:

- υποστηρίζει αρχικά **ENARTIA** και **ΕΓΝΑΤΙΑ ΟΔΟΣ**,
- χρησιμοποιεί τη SQL αποκλειστικά για `SELECT`,
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

## pdf2xxf: PDF -> XXF

Το πακέτο `pdf2xxf` διαβάζει τη δομή ενός XXF export της SoftOne και ξαναγράφει το αρχείο
πεδίο-πεδίο, χωρίς σταθερά offsets και χωρίς byte patching. Το format περιγράφει τον εαυτό του:
κάθε packet κουβαλά τον πίνακα πεδίων του (όνομα, τύπος, μέγεθος) και οι τιμές αποθηκεύονται
με πρόθεμα μήκους, οπότε τα μήκη και το framing υπολογίζονται ξανά σε κάθε εγγραφή.

```powershell
pdf2xxf "C:\Invoices\685258118.pdf" --template "C:\Templates\fedex.XXF" --out 685258118.XXF
```

Το `--template` είναι ένα πραγματικό export ενός ήδη καταχωρημένου παραστατικού του ίδιου
προμηθευτή. Το εργαλείο κρατά τα δεδομένα του προμηθευτή/ειδών από το template και
αντικαθιστά ημερομηνίες, αριθμό παραστατικού, γραμμές, ανάλυση ΦΠΑ και ποσά.

Για FedEx η γραμμή κάθε αποστολής επιλέγεται από την κατεύθυνση και τον ΦΠΑ:
εξαγωγή με ΦΠΑ `10016`, εξαγωγή χωρίς ΦΠΑ `10017`, εισαγωγή `10002`.

## Windows build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Το executable δημιουργείται στον φάκελο `dist`.

## Ασφάλεια

- Η σύνδεση SQL χρησιμοποιεί Windows authentication και `ApplicationIntent=ReadOnly`.
- Οι SQL εντολές του pilot είναι σταθερά, parameterized `SELECT`.
- Η αυτοματοποίηση απορρίπτει πραγματική αποθήκευση μέχρι να υπάρχει ολοκληρωμένο,
  επιβεβαιωμένο workflow profile.
- Πριν από πραγματική καταχώριση απαιτείται νέα ρητή έγκριση και δοκιμή ενός παραστατικού.
