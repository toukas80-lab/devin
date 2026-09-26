# Οδηγίες για Devin CLI (τοπικό PC γραφείου)

## Ρόλος
Όταν ο Θεόδωρος ρωτάει για δεδομένα ή στατιστικά του SoftOne (πωλήσεις, αγορές,
υπόλοιπα, προμηθευτές, είδη, παραστατικά), τρέξε **read-only** SQL στον τοπικό
SQL Server και δώσε την απάντηση σύντομα, σε πίνακα. Μην ζητάς διευκρινίσεις αν η
ερώτηση είναι εύλογα σαφής. Απάντα στα ελληνικά.

**Ταχύτητα:** στόχος 1-2 queries ανά ερώτηση. Χρησιμοποίησε τα έτοιμα queries
παρακάτω και **μην** κάνεις εξερεύνηση (COMPANY, FPRMS, INFORMATION_SCHEMA) εκτός αν
κάτι αποτύχει. Μην προσθέτεις συγκρίσεις/αναλύσεις που δεν ζητήθηκαν.

## Σύνδεση
- Instance: `.\SOFTONE` — Database: `FOUNTOUKAS`
- Login: `devin_ro` (read-only, `db_datareader`). Ο κωδικός βρίσκεται στη μεταβλητή
  περιβάλλοντος `SQLCMDPASSWORD` (user env var στα Windows), την οποία το `sqlcmd`
  διαβάζει μόνο του — **μην** χρησιμοποιείς `-P` και μην εκτυπώνεις ποτέ τον κωδικό.
- Shell: PowerShell. Εντολή (το UTF-8 + `-u` είναι απαραίτητα για τα ελληνικά):
  ```powershell
  [Console]::OutputEncoding=[Text.Encoding]::UTF8; sqlcmd -S .\SOFTONE -d FOUNTOUKAS -U devin_ro -W -u -w 300 -s "|" -Q "<query>"
  ```
  Αν λείπει το `sqlcmd`, γράψε το query σε αρχείο `q.sql` και τρέξε με Python/pyodbc
  (driver "ODBC Driver 17 for SQL Server"):
  ```powershell
  python -c "import os,pyodbc; c=pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SOFTONE;DATABASE=FOUNTOUKAS;UID=devin_ro;PWD='+os.environ['SQLCMDPASSWORD']); [print(r) for r in c.execute(open('q.sql',encoding='utf-8').read())]"
  ```
- ΜΟΝΟ `SELECT`. Ποτέ INSERT/UPDATE/DELETE/EXEC, ποτέ `SELECT *` σε μεγάλους πίνακες
  χωρίς `TOP`/`WHERE`. Η βάση είναι παραγωγική: κράτα τα queries ελαφριά. Μην βάζεις
  `NOLOCK` σε οικονομικά ποσά (μπορεί να δείξει μη οριστικοποιημένες κινήσεις).

## Εταιρείες (COMPANY) — ΣΗΜΑΝΤΙΚΟ
| COMPANY | Τι είναι | Χρήση |
|---|---|---|
| **3000** | Η εταιρεία που δουλεύει ο Θεόδωρος στο SoftOne (δεδομένα 2018–σήμερα) | **Default για όλα.** |
| 1000 / 1001 | Φουντούκας Θεόδωρος (ατομική) / ΜΟΝ ΙΚΕ | **Μην** τις χρησιμοποιείς εκτός αν ζητηθεί ρητά. |
| 2000 | «ΑΡΧΙΚΗ ΕΤΑΙΡΙΑ ΑΠΟ ΛΑΘΟΣ» | Αγνόησε. |

Πάντα `COMPANY = 3000` (όχι 1, όχι 1001). Οι πίνακες `SERIES`, `FPRMS`, `TRDR`, `MTRL`, `BRANCH`
έχουν κι αυτοί στήλη `COMPANY`: **κάθε JOIN πρέπει να περιλαμβάνει `AND x.COMPANY = f.COMPANY`**,
αλλιώς οι γραμμές διπλασιάζονται.

## Τύποι παραστατικών (FPRMS.TFPRMS) — τι μετράει ως πώληση
Το `SOSOURCE=1351` περιέχει ΚΑΙ δελτία αποστολής, παραγγελίες, προσφορές. Για
**τζίρο πωλήσεων** φίλτραρε με `FPRMS.TFPRMS`:
| TFPRMS | Τύπος | Πρόσημο |
|---|---|---|
| 102 | Τιμολόγιο / Τιμολόγιο Παροχής Υπηρεσιών | + |
| 103 | Τιμολόγιο-Δελτίο Αποστολής (ΤΔΑ) | + |
| 131 | Απόδειξη Λιανικής | + |
| 151, 152 | Πιστωτικό Τιμολόγιο | − |
| 181 | Απόδειξη Επιστροφής Λιανικής | − |
| 101 | Δελτίο Αποστολής (ΔΑ) | **όχι πώληση** (ακολουθεί τιμολόγιο) |
| 201 / 202 | Παραγγελία / Προσφορά-Κατάλογος | όχι πώληση |
| 104, 105, 154 | Παραλαβές / επιστροφές ΔΑ | όχι πώληση |
Το `FPRMS` **δεν** έχει στήλη `CODE` — μόνο `NAME`, `TFPRMS`. Μην επιλέγεις `SOVAL`/`SODATA`
(blob). Ακυρωτικά έχουν `ISCANCEL=1` στο FINDOC, το φίλτρο `ISCANCEL=0` τα κόβει.

## Βασικοί πίνακες SoftONE (schema dbo)
| Πίνακας | Τι είναι | Κλειδί / σημαντικές στήλες |
|---|---|---|
| `TRDR` | Συναλλασσόμενοι (πελάτες & προμηθευτές) | `TRDR`, `COMPANY`, `CODE`, `NAME`, `AFM`, `SODTYPE` (13=πελάτης, 12=προμηθευτής), `ISACTIVE`, `PAYMENT` |
| `MTRL` | Είδη / υπηρεσίες | `MTRL`, `COMPANY`, `CODE`, `NAME`, `SODTYPE` (51=είδος), `MTRCATEGORY`, `MTRGROUP`, `PRICER`, `PRICEW` |
| `FINDOC` | Επικεφαλίδες παραστατικών | `FINDOC`, `COMPANY`, `SOSOURCE` (1351=πωλήσεις, 1251=αγορές, 1361=εισπράξεις, 1261=πληρωμές), `FPRMS`, `SERIES`, `FINCODE` (π.χ. ΤΙΜ0000004), `TRNDATE`, `TRDR`, `SUMAMNT` (σύνολο με ΦΠΑ), `NETAMNT` (καθαρή), `VATAMNT`, `ISCANCEL`, `BRANCH` |
| `MTRLINES` | Γραμμές ειδών παραστατικών | `FINDOC`, `MTRL`, `QTY1`, `PRICE`, `LINEVAL` (καθαρή αξία γραμμής), `VATAMNT`, `DISC1PRC` |
| `ITELINES` | Γραμμές οικονομικών (πληρωμών/εισπράξεων) | `FINDOC`, `PAYMENT`, `LINEVAL` |
| `SERIES` | Σειρές παραστατικών | `SERIES`, `COMPANY`, `CODE`, `NAME`, `SOSOURCE`, `FPRMS` |
| `FPRMS` | Τύποι παραστατικών | `FPRMS`, `COMPANY`, `SOSOURCE`, `NAME`, `TFPRMS`, `ISDELIVERYNOTE` |
| `PAYMENT` | Τρόποι πληρωμής | `PAYMENT`, `CODE`, `NAME` |
| `MTRCATEGORY`, `MTRGROUP` | Κατηγορίες/ομάδες ειδών | `CODE`, `NAME` |
| `MTRTRN` | Κινήσεις ειδών (αποθήκη) | `MTRL`, `TRNDATE`, `QTY1`, `IMPVAL`/`EXPVAL`, `FINDOC` |
| `COMPANY`, `BRANCH` | Εταιρεία / υποκατάστημα | `COMPANY`, `BRANCH`, `NAME` |

Σημειώσεις:
- Αν αμφιβάλλεις για όνομα στήλης, τρέξε
  `SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='FINDOC'`.
- Ημερομηνίες: `TRNDATE` datetime → φίλτρα με `>= 'YYYY-MM-01' AND < 'YYYY-MM+1-01'`.
- Ποσά σε ευρώ: `CAST(SUM(x) AS decimal(18,2))` (όχι ROUND, δίνει 0.0999999).

## Έτοιμα queries
Πωλήσεις (τζίρος) μήνα — π.χ. Αύγουστος 2026:
```sql
SELECT p.NAME AS Τύπος, COUNT(*) AS Παραστατικά,
       CAST(SUM(f.NETAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END) AS decimal(18,2)) AS Καθαρή,
       CAST(SUM(f.SUMAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END) AS decimal(18,2)) AS Σύνολο
FROM dbo.FINDOC f
JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.ISCANCEL=0
  AND p.TFPRMS IN (102,103,131,151,152,181)
  AND f.TRNDATE >= '2026-08-01' AND f.TRNDATE < '2026-09-01'
GROUP BY p.NAME ORDER BY Σύνολο DESC;
```
Πωλήσεις ανά μήνα (τρέχον έτος):
```sql
SELECT FORMAT(f.TRNDATE,'yyyy-MM') AS Μήνας, COUNT(*) AS Παραστατικά,
       CAST(SUM(f.NETAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END) AS decimal(18,2)) AS Καθαρή,
       CAST(SUM(f.SUMAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END) AS decimal(18,2)) AS Σύνολο
FROM dbo.FINDOC f
JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.ISCANCEL=0
  AND p.TFPRMS IN (102,103,131,151,152,181)
  AND f.TRNDATE >= DATEFROMPARTS(YEAR(GETDATE()),1,1)
GROUP BY FORMAT(f.TRNDATE,'yyyy-MM') ORDER BY 1;
```
Top πελάτες περιόδου:
```sql
SELECT TOP 10 t.CODE, t.NAME, COUNT(*) AS Παραστατικά,
       CAST(SUM(f.SUMAMNT * CASE WHEN p.TFPRMS IN (151,152,181) THEN -1 ELSE 1 END) AS decimal(18,2)) AS Σύνολο
FROM dbo.FINDOC f
JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
JOIN dbo.TRDR t ON t.TRDR=f.TRDR AND t.COMPANY=f.COMPANY
WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.ISCANCEL=0
  AND p.TFPRMS IN (102,103,131,151,152,181)
  AND f.TRNDATE >= '2026-08-01' AND f.TRNDATE < '2026-09-01'
GROUP BY t.CODE, t.NAME ORDER BY Σύνολο DESC;
```
Αγορές ανά προμηθευτή (τρέχον έτος):
```sql
SELECT TOP 20 t.CODE, t.NAME, t.AFM, COUNT(*) AS Παραστατικά,
       CAST(SUM(f.SUMAMNT) AS decimal(18,2)) AS Σύνολο
FROM dbo.FINDOC f
JOIN dbo.TRDR t ON t.TRDR=f.TRDR AND t.COMPANY=f.COMPANY
WHERE f.COMPANY=3000 AND f.SOSOURCE=1251 AND f.ISCANCEL=0
  AND f.TRNDATE >= DATEFROMPARTS(YEAR(GETDATE()),1,1)
GROUP BY t.CODE,t.NAME,t.AFM ORDER BY Σύνολο DESC;
```
Top είδη σε πωλήσεις:
```sql
SELECT TOP 20 m.CODE, m.NAME,
       CAST(SUM(l.QTY1) AS decimal(18,2)) AS Ποσότητα, CAST(SUM(l.LINEVAL) AS decimal(18,2)) AS Καθαρή
FROM dbo.MTRLINES l
JOIN dbo.FINDOC f ON f.FINDOC=l.FINDOC
JOIN dbo.FPRMS p ON p.FPRMS=f.FPRMS AND p.COMPANY=f.COMPANY AND p.SOSOURCE=f.SOSOURCE
JOIN dbo.MTRL m ON m.MTRL=l.MTRL AND m.COMPANY=f.COMPANY
WHERE f.COMPANY=3000 AND f.SOSOURCE=1351 AND f.ISCANCEL=0 AND p.TFPRMS IN (102,103,131)
  AND f.TRNDATE >= DATEFROMPARTS(YEAR(GETDATE()),1,1)
GROUP BY m.CODE,m.NAME ORDER BY Καθαρή DESC;
```
Αναζήτηση προμηθευτή με ΑΦΜ:
```sql
SELECT TRDR, CODE, NAME, AFM FROM dbo.TRDR
WHERE COMPANY=3000 AND SODTYPE=12 AND REPLACE(AFM,'EL','') = '999082935';
```

## Setup (μία φορά)
1. Τρέξε `scripts/sql/create_readonly_login.sql` στο SSMS (άλλαξε το password).
2. PowerShell: `setx SQLCMDPASSWORD "<το password>"` και άνοιξε νέο PowerShell.
3. Έλεγχος: `sqlcmd -S .\SOFTONE -d FOUNTOUKAS -U devin_ro -Q "SELECT TOP 1 CODE,NAME FROM dbo.TRDR"`.
   Αν λείπει το `sqlcmd`: https://learn.microsoft.com/sql/tools/sqlcmd/sqlcmd-utility (ή `winget install sqlcmd`).
4. Devin CLI (PowerShell): `irm https://static.devin.ai/cli/setup.ps1 | iex`, μετά `cd` στον
   φάκελο του repo και `devin`. Ρώτα ό,τι θέλεις.

## Υπόλοιπο repo
Το `softone-pilot` (PDF → SoftOne) παραμένει ως έχει: lint `ruff check src tests`,
tests `PYTHONPATH=src python -m pytest -q`.
