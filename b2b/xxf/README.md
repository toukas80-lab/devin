# B2B XXF (SoftOne import) — reference

`template_7021.XXF` = ΠΑΡ 7021, company 1001, customer 3837, 2 lines (03137 x1 @5, 02576 x2 @10),
STDSALDOC group only. **Imported OK in SoftOne** as ΠΑΡ0000891 (auto number, «B2B W-000007» στην αιτιολογία).
`python3 mk_ref.py` regenerates it byte-for-byte from itself (= the reference algorithm).

## File format (validated)
- bytes 0..0x1b: header (copy as is).
- then groups: u8 len + name (cp1253) + u32 table count + per table: u32 blob len + blob.
- table blob: `XSF_`... byte[8]=name len, name, u32 hdr + u16 field count, per field: 4×u16 (type,size,off,attr) + name\0.
  Then per row: byte 00 + u32 row index (1,2,3…) + each field value in field order.
- value: 1 byte length L (0 = NULL); L=0xFE → u16 length follows; L=0xFF → u32 length follows; then L raw bytes.
  types: 3/1027 int32 LE, 2 int16 LE, 6 double LE, 11 datetime = double ms
  (= (days since 0001-01-01, with 0001-01-01 = day 1) × 86400000 + ms of day, local Athens time), 1/513 text cp1253.
- A table with 0 rows ends right after the field list. Length of the whole file / blobs may change freely
  (rebuild is fine; this was what failed only when the per-row index was wrong).

## What changes per order (see mk_ref.py)
FINDOC row: TRDR (=SoftOne TRDR id = portal customers.id), TRDR_CODE, TRNDATE/BGDOCDATE/INSDATEN (date 00:00),
APPRVDATE/BGDOCDATE1/INSDATE/SOTIME/UPDDATE (order datetime), FISCPRD (year), PERIOD (month),
COMMENTS = 'B2B W-000008', REMARKS = 'W-000008', PAYMENT = customer TRDR.PAYMENT (NULL if none — SoftOne does NOT
fill it from the card), totals TURNOVR/TTURNOVR/LTURNOVR/NETAMNT/TNETAMNT/LNETAMNT = net,
VATAMNT/TVATAMNT/LVATAMNT = vat, SUMAMNT/SUMTAMNT/SUMLAMNT = net+vat. Keep SERIESNUM=0, FINCODE/TAXSERIESNUM NULL,
ISPRINT=0, FINDOC=255043 (deleted doc; SoftOne gives a new id), everything else as template.
MTRDOC: QTY = QTY1 = sum of qty.
MTRLINES: one row per line from template row 1: MTRLINES=LINENUM=i, MTRL (=portal items.id), MTRL_CODE, VAT (SoftOne
VAT code, 1410 = 24%), MTRUNIT (MTRL.MTRUNIT1), QTY=QTY1=qty, PRICE=PRICE1=unit price (portal eff price, excl. VAT),
LINEVAL/LLINEVAL/NETLINEVAL/LNETLINEVAL/TRNLINEVAL/LTRNLINEVAL = line net, VATAMNT/LVATAMNT = line vat,
SXPERC = net+vat.
VATANAL: one row per VAT code: LINENUM=i, VAT, SUBVAL=LSUBVAL=net, VATVAL=LVATVAL=vat.
FINPAYTERMS, SNLINES, FPAYTRMS2, EXPANAL, ABCTRNLINES: 0 rows.
