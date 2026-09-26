# Οδηγίες για Devin CLI (τοπικό PC γραφείου)

## Ρόλος
Όταν ο Θεόδωρος ρωτάει για δεδομένα ή στατιστικά του SoftOne (πωλήσεις, αγορές,
υπόλοιπα, προμηθευτές, είδη, παραστατικά), τρέξε **read-only** SQL στον τοπικό
SQL Server και δώσε την απάντηση σύντομα, σε πίνακα. Μην ζητάς διευκρινίσεις αν η
ερώτηση είναι εύλογα σαφής. Απάντα στα ελληνικά.

## Σύνδεση
- Instance: `.\SOFTONE` — Database: `FOUNTOUKAS`
- Login: `devin_ro` (read-only, `db_datareader`). Password στη μεταβλητή περιβάλλοντος
  `SOFTONE_SQL_PASSWORD` (user env var στα Windows). Μην την εκτυπώνεις ποτέ.
- Εντολή:
  ```
  sqlcmd -S .\SOFTONE -d FOUNTOUKAS -U devin_ro -P "%SOFTONE_SQL_PASSWORD%" -W -s "|" -Q "<query>"
  ```
  PowerShell: `-P "$env:SOFTONE_SQL_PASSWORD"`. Αν λείπει το `sqlcmd`, εναλλακτικά
  `PYTHONPATH=src python -c` με `pyodbc` (driver "ODBC Driver 17 for SQL Server").
- ΜΟΝΟ `SELECT`. Ποτέ INSERT/UPDATE/DELETE/EXEC, ποτέ `SELECT *` σε μεγάλους πίνακες
  χωρίς `TOP`/`WHERE`. Βάζε πάντα `WITH (NOLOCK)`; η βάση είναι παραγωγική.

## Βασικοί πίνακες SoftONE (schema dbo)
| Πίνακας | Τι είναι | Κλειδί / σημαντικές στήλες |
|---|---|---|
| `TRDR` | Συναλλασσόμενοι (πελάτες & προμηθευτές) | `TRDR`, `CODE`, `NAME`, `AFM`, `SODTYPE` (13=πελάτης, 12=προμηθευτής), `ISACTIVE`, `PAYMENT` |
| `MTRL` | Είδη / υπηρεσίες | `MTRL`, `CODE`, `NAME`, `SODTYPE` (51=είδος), `MTRCATEGORY`, `MTRGROUP`, `PRICER` (τιμή λιανικής), `PRICEW` |
| `FINDOC` | Επικεφαλίδες παραστατικών (πωλήσεις, αγορές, εισπράξεις, πληρωμές) | `FINDOC`, `SOSOURCE` (1351=πωλήσεις, 1251=αγορές, 1361=εισπράξεις, 1261=πληρωμές), `FPRMS`, `SERIES`, `SERIESNUM`, `FINCODE`, `TRNDATE`, `TRDR`, `SUMAMNT` (σύνολο), `NETAMNT` (καθαρή), `VATAMNT`, `ISCANCEL`, `COMPANY`, `BRANCH` |
| `MTRLINES` | Γραμμές ειδών παραστατικών | `FINDOC`, `MTRL`, `QTY1`, `PRICE`, `LINEVAL` (καθαρή αξία γραμμής), `VATAMNT`, `DISC1PRC` |
| `ITELINES` | Γραμμές οικονομικών (πληρωμών/εισπράξεων) | `FINDOC`, `PAYMENT`, `LINEVAL` |
| `SERIES` | Σειρές παραστατικών | `SERIES`, `CODE`, `NAME`, `SOSOURCE`, `FPRMS` |
| `FPRMS` | Τύποι παραστατικών | `FPRMS`, `CODE`, `NAME`, `SOSOURCE` |
| `PAYMENT` | Τρόποι πληρωμής | `PAYMENT`, `CODE`, `NAME` |
| `MTRCATEGORY`, `MTRGROUP` | Κατηγορίες/ομάδες ειδών | `CODE`, `NAME` |
| `MTRTRN` | Κινήσεις ειδών (αποθήκη) | `MTRL`, `TRNDATE`, `QTY1`, `IMPVAL`/`EXPVAL`, `FINDOC` |
| `TRDFINDATA` / `TRDRBALANCE` (αν υπάρχει) | Υπόλοιπα συναλλασσομένων | `TRDR`, `DEBIT`, `CREDIT` |
| `COMPANY`, `BRANCH` | Εταιρεία / υποκατάστημα | `COMPANY`, `BRANCH`, `NAME` |

Σημειώσεις:
- Αν αμφιβάλλεις για όνομα στήλης, τρέξε πρώτα
  `SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='FINDOC'`.
- Πάντα φίλτρο `ISCANCEL = 0` στο `FINDOC`, και `COMPANY = 1` (μία εταιρεία).
- Ημερομηνίες: `TRNDATE` είναι datetime → `CONVERT(date, TRNDATE)`.
- Ποσά είναι σε ευρώ; στρογγύλευε σε 2 δεκαδικά.

## Έτοιμα queries
Πωλήσεις ανά μήνα (τρέχον έτος):
```sql
SELECT FORMAT(TRNDATE,'yyyy-MM') AS Μήνας,
       COUNT(*) AS Παραστατικά,
       ROUND(SUM(NETAMNT),2) AS Καθαρή, ROUND(SUM(SUMAMNT),2) AS Σύνολο
FROM dbo.FINDOC WITH (NOLOCK)
WHERE SOSOURCE=1351 AND ISCANCEL=0 AND COMPANY=1
  AND TRNDATE >= DATEFROMPARTS(YEAR(GETDATE()),1,1)
GROUP BY FORMAT(TRNDATE,'yyyy-MM') ORDER BY 1;
```
Αγορές ανά προμηθευτή (τρέχον έτος):
```sql
SELECT TOP 20 t.CODE, t.NAME, t.AFM,
       COUNT(*) AS Παραστατικά, ROUND(SUM(f.SUMAMNT),2) AS Σύνολο
FROM dbo.FINDOC f WITH (NOLOCK)
JOIN dbo.TRDR t WITH (NOLOCK) ON t.TRDR=f.TRDR
WHERE f.SOSOURCE=1251 AND f.ISCANCEL=0 AND f.COMPANY=1
  AND f.TRNDATE >= DATEFROMPARTS(YEAR(GETDATE()),1,1)
GROUP BY t.CODE,t.NAME,t.AFM ORDER BY Σύνολο DESC;
```
Top είδη σε πωλήσεις:
```sql
SELECT TOP 20 m.CODE, m.NAME,
       ROUND(SUM(l.QTY1),2) AS Ποσότητα, ROUND(SUM(l.LINEVAL),2) AS Καθαρή
FROM dbo.MTRLINES l WITH (NOLOCK)
JOIN dbo.FINDOC f WITH (NOLOCK) ON f.FINDOC=l.FINDOC
JOIN dbo.MTRL m WITH (NOLOCK) ON m.MTRL=l.MTRL
WHERE f.SOSOURCE=1351 AND f.ISCANCEL=0 AND f.COMPANY=1
  AND f.TRNDATE >= DATEFROMPARTS(YEAR(GETDATE()),1,1)
GROUP BY m.CODE,m.NAME ORDER BY Καθαρή DESC;
```
Αναζήτηση προμηθευτή με ΑΦΜ:
```sql
SELECT TRDR, CODE, NAME, AFM FROM dbo.TRDR WITH (NOLOCK)
WHERE REPLACE(AFM,'EL','') = '999082935';
```

## Setup (μία φορά)
1. Τρέξε `scripts/sql/create_readonly_login.sql` στο SSMS (άλλαξε το password).
2. Windows: `setx SOFTONE_SQL_PASSWORD "<το password>"` και άνοιξε νέο terminal.
3. Έλεγχος: `sqlcmd -S .\SOFTONE -d FOUNTOUKAS -U devin_ro -P "%SOFTONE_SQL_PASSWORD%" -Q "SELECT TOP 1 CODE,NAME FROM dbo.TRDR"`.
4. Άνοιξε το Devin CLI σε αυτόν τον φάκελο και ρώτα ό,τι θέλεις.

## Υπόλοιπο repo
Το `softone-pilot` (PDF → SoftOne) παραμένει ως έχει: lint `ruff check src tests`,
tests `PYTHONPATH=src python -m pytest -q`.
