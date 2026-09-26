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

Dry-run με read-only SQL:

```powershell
softone-pilot dry-run "C:\Invoices" --config config\local.json
```

Παραγωγή αρχείων για το SoftOne DImport script (Advanced Javascript):

```powershell
softone-pilot make-txt "C:\Invoices" --config config\local.json --out-dir C:\Soft1
```

Γράφει `C:\Soft1\DEVIN-EXP.txt` (δαπάνες, `kind: "expense"`) και/ή
`C:\Soft1\DEVIN-IMPORT.txt` (αγορές ειδών, `kind: "purchase"`, με `item_map`
κωδικός προμηθευτή -> κωδικός είδους SoftOne). Δαπάνες με λογαριασμό ανά γραμμή
(π.χ. FEDEX: εξαγωγή/εισαγωγή 24%/0%, δασμοί `duty`) ρυθμίζονται με `line_codes`
κατηγορία -> λογαριασμός, αντί για ενιαίο `line_code`. Τιμολόγια σε USD (COGNITION,
reverse charge) μετατρέπονται σε EUR με την ισοτιμία αναφοράς ΕΚΤ της ημέρας του
τιμολογίου (λήψη από ecb.europa.eu) ή με `--rate 0,8585` (EUR ανά 1 USD)· η αιτιολογία
κρατά το `$20,00 X 0,8585`. Ποσοστά ΦΠΑ με πολλές κατηγορίες στη SoftOne (π.χ. 0%)
αντιστοιχίζονται σε συγκεκριμένο VAT id με `vat_ids` (`{"0": "0"}` -> στήλη `ID:0`, όπως οι ιστορικές γραμμές 0%).
Το `trdr_code` μπορεί να είναι και `AFM:<ΑΦΜ>` — τότε ο πιστωτής βρίσκεται από το
`DevinExpMakeHead` μέσω ΑΦΜ (π.χ. FINLOUP LEASING II, που έχει ξεχωριστό ΑΦΜ από τη Leasing I).
Παραστατικό χωρίς πλήρη ρύθμιση
(πιστωτής, σειρά, λογαριασμός ή αντιστοίχιση είδους) αναφέρεται ως ERROR και
δεν γράφεται. Στη συνέχεια στο SoftOne (Advanced Javascript, module `DImport`,
κώδικας στο `scripts/softone/DevinImport.js`): `DevinDryRun` (προέλεγχος: στήνει τα
παραστατικά στη μνήμη μέσω PURDOC/LINCREDOC, δείχνει σύνολα, δεν αποθηκεύει τίποτα) ->
`DevinExpMakeHead`/`DevinMakeHead` -> οδηγός ASCII Import
(`D TEST ΔΑΠΑΝΕΣ` / `D TEST ΑΓΟΡΕΣ`) -> `DevinExpAddLines`/`DevinAddLines`.
Η αποθήκευση με ένα βήμα (`DevinAll`) είναι απενεργοποιημένη: στη 6.00.622 το `DBPOST`
των αντικειμένων αντικαθιστά το «Παραστατικό» (FINCODE) με τον αυτόματο αριθμό της σειράς
(ΤΔΕΕ/221) και ο αριθμός του προμηθευτή χάνεται — μόνο ο οδηγός ASCII και η φόρμα τον
κρατούν (δοκιμάστηκε σε FINDOC 253801/253802).

Καθημερινή χρήση χωρίς γραμμή εντολών (`DEVIN-PDF.exe`, βλ. Windows build):
ρίξε τα PDF στο `C:\Soft1\PDF` και τρέξε το .exe. Διαβάζει όλα τα PDF, γράφει
`DEVIN-EXP.txt` / `DEVIN-IMPORT.txt` / `DEVIN-REPORT.txt` στο `C:\Soft1`, μετακινεί
τα επιτυχή PDF στο `C:\Soft1\PDF\ΕΓΙΝΑΝ\<ημερομηνία>` και αφήνει τα προβληματικά
στη θέση τους με τον λόγο στην αναφορά. Οι γραμμές προηγούμενου τρεξίματος μένουν
στα txt (η SoftOne κάνει SKIP όσα έχουν ήδη περάσει· το ίδιο παραστατικό ξανά αντικαθιστά
τις παλιές γραμμές του) — σβήσε το txt για καθαρή αρχή. Στην πρώτη εκτέλεση δημιουργεί το
`C:\Soft1\devin-config.json` (αντιστοιχίσεις προμηθευτών, επεξεργάσιμο).
Από γραμμή εντολών: `devin-pdf [βάση]`.

Γραφικό περιβάλλον:

```powershell
softone-pilot-gui
```

Καταγραφή του UI Automation control tree του ήδη ανοικτού SoftOne:

```powershell
softone-pilot inspect-softone --workflow config\softone_workflow.example.json
```

Η παραπάνω εντολή δεν κάνει click και δεν αλλάζει δεδομένα.

## Windows build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Το executable δημιουργείται στο `dist\DEVIN-PDF.exe`. Το ίδιο κάνει το GitHub Actions
workflow `Build DEVIN-PDF.exe` σε κάθε push (artifact `DEVIN-PDF`).

## Ασφάλεια

- Η σύνδεση SQL χρησιμοποιεί Windows authentication και `ApplicationIntent=ReadOnly`.
- Οι SQL εντολές του pilot είναι σταθερά, parameterized `SELECT`.
- Η αυτοματοποίηση απορρίπτει πραγματική αποθήκευση μέχρι να υπάρχει ολοκληρωμένο,
  επιβεβαιωμένο workflow profile.
- Πριν από πραγματική καταχώριση απαιτείται νέα ρητή έγκριση και δοκιμή ενός παραστατικού.
