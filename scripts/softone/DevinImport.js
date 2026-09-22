// DevinImport - SoftOne Advanced Javascript (module DImport)
//
// Daily use (one step, see ONE-STEP IMPORT at the end):
//   DevinDryRun  -> shows what would be created from C:\Soft1\DEVIN-EXP.txt + DEVIN-IMPORT.txt, saves nothing
//   DevinAll     -> creates the documents (header + all lines) via the SoftOne objects; SKIP if already there
//
// Fallback / legacy hybrid purchase import (no SQL writes, SoftOne-native only):
//   step 1  ASCII Import wizard : C:\Soft1\DEVIN-HEAD.txt   (1 row per document = header + FIRST line;
//           field 4 must be the FULL code e.g. 'ΤΔΑ-017838' because the wizard stores it verbatim)
//           -> creates the document with the correct FINCODE ("Παραστατικό").
//   step 2  DevinAddLines       : C:\Soft1\DEVIN-IMPORT.txt (ALL rows, same 7-field format)
//           -> locates each document (supplier + FINCODE) and appends lines 2..n via the PURDOC object.
//              An edit that does not touch FINCODE keeps it (verified).
//
// Row format of DEVIN-IMPORT.txt: date;series;supplier;docnum;item;qty;price[;vat]
//   series   : code 'ΤΔΑ' (or internal id 2062)
//   supplier : supplier code '0273'  |  'AFM:094012345'  |  'ID:169439'
//   item     : item code '03762'     |  'ID:155432'
//   docnum   : used verbatim, e.g. '017838' or 'E1L-324247'; FINCODE = <series code>-<docnum>
//   vat      : percentage '24' / '13' / '6' (default 24)  |  'ID:1410'
//   disc     : optional 9th field, line discount % (e.g. '25'), default 0
// All codes are resolved with read-only SQL; an unknown/ambiguous code stops the run before any write.
// DEVIN-HEAD.txt (written by DevinMakeHead) always contains the resolved internal ids for the wizard.
//
// Result per document: OK / SKIP / ERR. Idempotent: a complete document is SKIPped.

function DevinNum(s) {
    return parseFloat(String(s).replace(',', '.'));
}

// sql must return one column aliased ID; params: 1 or 2 values
function DevinOne(sql, params, what) {
    var ds = params.length == 1 ? X.GETSQLDATASET(sql, params[0]) : X.GETSQLDATASET(sql, params[0], params[1]);
    var key = params[params.length - 1];
    if (ds.RECORDCOUNT == 0) throw new Error(what + ' not found: ' + key);
    if (ds.RECORDCOUNT > 1) throw new Error(what + ' ambiguous (' + ds.RECORDCOUNT + ' matches): ' + key);
    return parseInt(ds.ID, 10);
}

function DevinSeries(s) {
    s = String(s).replace(/^\s+|\s+$/g, '');
    if (/^ID:/i.test(s)) return parseInt(s.substring(3), 10);
    if (/^\d+$/.test(s)) return parseInt(s, 10);
    return DevinOne('SELECT SERIES AS ID FROM SERIES WHERE COMPANY=:1 AND SOSOURCE=1251 AND CODE=:2', [X.SYS.COMPANY, s], 'Series');
}

function DevinTrdr(s) {
    s = String(s).replace(/^\s+|\s+$/g, '');
    if (/^ID:/i.test(s)) return parseInt(s.substring(3), 10);
    if (/^AFM:/i.test(s))
        return DevinOne('SELECT TRDR AS ID FROM TRDR WHERE COMPANY=:1 AND SODTYPE=12 AND ISACTIVE=1 AND AFM=:2', [X.SYS.COMPANY, s.substring(4)], 'Supplier AFM');
    return DevinOne('SELECT TRDR AS ID FROM TRDR WHERE COMPANY=:1 AND SODTYPE=12 AND CODE=:2', [X.SYS.COMPANY, s], 'Supplier code');
}

function DevinMtrl(s) {
    s = String(s).replace(/^\s+|\s+$/g, '');
    if (/^ID:/i.test(s)) return parseInt(s.substring(3), 10);
    return DevinOne('SELECT MTRL AS ID FROM MTRL WHERE COMPANY=:1 AND SODTYPE=51 AND CODE=:2', [X.SYS.COMPANY, s], 'Item code');
}

function DevinVat(s) {
    s = String(s == null ? '' : s).replace(/^\s+|\s+$/g, '');
    if (s == '') s = '24';
    if (/^ID:/i.test(s)) return parseInt(s.substring(3), 10);
    if (parseInt(s, 10) > 100) return parseInt(s, 10);
    return DevinOne('SELECT VAT AS ID FROM VAT WHERE PERCNT=:1', [DevinNum(s)], 'VAT %');
}

function DevinReadRows(fileName) {
    var rows = [];
    var f = X.EXEC('CODE:PILib.OpenText', fileName, 65001);
    try {
        while (!X.EXEC('CODE:PILib.EOF', f)) {
            var line = String(X.EXEC('CODE:PILib.ReadLine', f)).replace(/^\uFEFF/, '');
            if (line.replace(/\s/g, '') == '') continue;
            var p = line.split(';');
            if (p.length < 7) throw new Error('Bad line (need 7+ fields): ' + line);
            rows.push({
                trndate: p[0], series: DevinSeries(p[1]), trdr: DevinTrdr(p[2]),
                docnum: p[3].replace(/^\s+|\s+$/g, ''),
                mtrl: DevinMtrl(p[4]), qty: DevinNum(p[5]),
                price: DevinNum(p[6]), vat: DevinVat(p.length > 7 ? p[7] : ''),
                disc: (p.length > 8 && p[8].replace(/\s/g, '') != '') ? DevinNum(p[8]) : 0
            });
        }
    }
    finally {
        X.EXEC('CODE:PILib.CloseText', f);
    }
    return rows;
}

function DevinGroup(rows) {
    var docs = [], byKey = {};
    for (var i = 0; i < rows.length; i++) {
        var r = rows[i], k = r.trdr + '|' + r.series + '|' + r.docnum;
        if (!byKey[k]) {
            byKey[k] = { trndate: r.trndate, series: r.series, trdr: r.trdr, docnum: r.docnum, sosource: r.sosource || 1251, lines: [] };
            docs.push(byKey[k]);
        }
        byKey[k].lines.push(r);
    }
    return docs;
}

function DevinFincode(d) {
    // SERIES key is COMPANY + SOSOURCE + SERIES (same number exists in several modules)
    var ds = X.GETSQLDATASET('SELECT CODE FROM SERIES WHERE COMPANY=:1 AND SOSOURCE=:2 AND SERIES=:3', X.SYS.COMPANY, d.sosource, d.series);
    if (ds.RECORDCOUNT != 1) throw new Error('Series ' + d.series + ' not found in module ' + d.sosource);
    return String(ds.CODE) + '-' + d.docnum;
}

// Writes DEVIN-HEAD.txt (first row of every document) from DEVIN-IMPORT.txt, for the wizard.
function DevinMakeHead(fileName) {
    if (!fileName) fileName = 'C:\\Soft1\\DEVIN-IMPORT.txt';
    var headName = fileName.replace(/DEVIN-IMPORT\.txt$/i, 'DEVIN-HEAD.txt');
    if (headName == fileName) headName = fileName + '.head.txt';
    var docs = DevinGroup(DevinReadRows(fileName));
    var out = [], log = [];
    for (var i = 0; i < docs.length; i++) {
        var L = docs[i].lines[0], d = docs[i], fincode = DevinFincode(d);
        var n = parseInt(X.SQL(
            'SELECT COUNT(*) FROM FINDOC WHERE COMPANY=:1 AND SOSOURCE=1251 AND TRDR=:2 AND FINCODE=:3',
            X.SYS.COMPANY, d.trdr, fincode), 10);
        if (n > 0) { log.push('SKIP ' + fincode + ' (already exists, not written to HEAD)'); continue; }
        var row = [d.trndate, d.series, d.trdr, fincode, L.mtrl,
            String(L.qty).replace('.', ','), String(L.price).replace('.', ','), L.vat,
            String(L.disc).replace('.', ',')].join(';');
        out.push(row);
        log.push('HEAD ' + row);
    }
    var f = X.EXEC('CODE:PILib.CreateText', headName, 28597); // ISO-8859-7 = wizard code page 928
    try {
        for (var j = 0; j < out.length; j++) X.CALLPUBLISHED('PILib.WriteLine', f, out[j]);
    }
    finally {
        X.EXEC('CODE:PILib.CloseText', f);
    }
    return 'Wrote ' + out.length + ' of ' + docs.length + ' header row(s) to ' + headName +
        (out.length == 0 ? '\nNothing new - do NOT run the wizard.' : '\nRun the wizard with this file, then DevinAddLines.') +
        '\n' + log.join('\n');
}

function DevinAddLines(fileName) {
    if (!fileName) fileName = 'C:\\Soft1\\DEVIN-IMPORT.txt';
    var docs = DevinGroup(DevinReadRows(fileName));
    var out = ['File: ' + fileName, 'Docs in file: ' + docs.length];
    for (var i = 0; i < docs.length; i++) {
        var d = docs[i], fincode = DevinFincode(d);
        try {
            var ds = X.GETSQLDATASET(
                'SELECT FINDOC FROM FINDOC WHERE COMPANY=:1 AND SOSOURCE=1251 AND TRDR=:2 AND FINCODE=:3 ORDER BY FINDOC',
                X.SYS.COMPANY, d.trdr, fincode);
            if (ds.RECORDCOUNT == 0) { out.push('ERR  ' + fincode + ': header not found (run the ASCII Import wizard first)'); continue; }
            if (ds.RECORDCOUNT > 1) { out.push('ERR  ' + fincode + ': ' + ds.RECORDCOUNT + ' documents with this code for the supplier - check manually'); continue; }
            var id = parseInt(ds.FINDOC, 10);
            var have = parseInt(X.SQL('SELECT COUNT(*) FROM MTRLINES WHERE FINDOC=:1', id), 10);
            if (have >= d.lines.length) { out.push('SKIP ' + fincode + ' -> FINDOC ' + id + ' (already ' + have + ' lines)'); continue; }
            if (have != 1) { out.push('ERR  ' + fincode + ' -> FINDOC ' + id + ': has ' + have + ' lines, expected 1 - check manually'); continue; }
            var firstMtrl = parseInt(X.SQL('SELECT MTRL FROM MTRLINES WHERE FINDOC=:1', id), 10);
            if (firstMtrl != d.lines[0].mtrl) { out.push('ERR  ' + fincode + ' -> FINDOC ' + id + ': first line MTRL ' + firstMtrl + ' <> file ' + d.lines[0].mtrl); continue; }

            var obj = X.CREATEOBJFORM('PURDOC');
            try {
                obj.DBLOCATE(id);
                var lns = obj.FindTable('ITELINES');
                for (var j = 1; j < d.lines.length; j++) {
                    var L = d.lines[j];
                    lns.Append;
                    lns.MTRL = L.mtrl;
                    lns.QTY1 = L.qty;
                    lns.PRICE = L.price;
                    lns.VAT = L.vat;
                    if (L.disc) lns.DISC1PRC = L.disc;
                    lns.WHOUSE = 1000;
                    lns.Post;
                }
                var r = obj.DBPOST;
                if (!r) throw new Error(String(obj.GETLASTERROR));
            }
            finally {
                obj.FREE;
            }
            var now = X.GETSQLDATASET(
                'SELECT FINCODE, (SELECT COUNT(*) FROM MTRLINES M WHERE M.FINDOC=F.FINDOC) AS LINES, NETAMNT, VATAMNT, SUMAMNT FROM FINDOC F WHERE FINDOC=:1', id);
            out.push('OK   ' + fincode + ' -> FINDOC ' + id + ': added ' + (d.lines.length - 1) + ' line(s), now ' + now.JSON);
        }
        catch (e) {
            out.push('ERR  ' + fincode + ': ' + e.message);
        }
    }
    return out.join('\n');
}

// Read-only: shows header + lines of existing purchase documents with this FINCODE (any supplier),
// in the same codes the txt file uses. Default: the invoice under test.
function DevinShowDoc(fincode) {
    if (!fincode) fincode = 'ΤΔΑ-017838';
    var out = ['FINCODE ' + fincode];
    var h = X.GETSQLDATASET(
        'SELECT F.FINDOC, F.TRNDATE, S.CODE AS SERIESCODE, T.CODE AS TRDRCODE, T.NAME, T.AFM, F.NETAMNT, F.VATAMNT, F.SUMAMNT ' +
        'FROM FINDOC F JOIN SERIES S ON S.SERIES=F.SERIES AND S.COMPANY=F.COMPANY JOIN TRDR T ON T.TRDR=F.TRDR AND T.COMPANY=F.COMPANY AND T.SODTYPE=12 ' +
        'WHERE F.COMPANY=:1 AND F.SOSOURCE=1251 AND F.FINCODE=:2 ORDER BY F.FINDOC', X.SYS.COMPANY, fincode);
    out.push('Documents: ' + h.RECORDCOUNT);
    h.FIRST;
    while (!h.EOF) {
        out.push('--- FINDOC ' + h.FINDOC + '  ' + h.TRNDATE + '  ' + h.SERIESCODE + '  supplier ' + h.TRDRCODE + ' ' + h.NAME +
            ' (AFM ' + h.AFM + ')  net ' + h.NETAMNT + ' vat ' + h.VATAMNT + ' total ' + h.SUMAMNT);
        var l = X.GETSQLDATASET(
            'SELECT L.LINENUM, M.CODE, M.NAME, L.QTY1, L.PRICE, L.DISC1PRC, L.LINEVAL, L.VATAMNT, V.PERCNT ' +
            'FROM MTRLINES L JOIN MTRL M ON M.MTRL=L.MTRL LEFT JOIN VAT V ON V.VAT=L.VAT ' +
            'WHERE L.FINDOC=:1 ORDER BY L.LINENUM', h.FINDOC);
        l.FIRST;
        while (!l.EOF) {
            out.push('    ' + l.CODE + ' | ' + l.NAME + ' | qty ' + l.QTY1 + ' | price ' + l.PRICE + ' | disc% ' + l.DISC1PRC +
                ' | value ' + l.LINEVAL + ' | vat% ' + l.PERCNT);
            l.NEXT;
        }
        h.NEXT;
    }
    return out.join('\n');
}

// Read-only: discovers how expense documents (SOSOURCE 1261) are stored: series, latest docs,
// which tables hold their lines, and which object can DBLOCATE them.
function DevinProbeExp(sosource) {
    sosource = parseInt(sosource || 1653, 10); // 1653 = Ειδικές πιστωτών, 1261 = Δαπάνες
    var out = ['SOSOURCE ' + sosource], co = X.SYS.COMPANY;
    var s = X.GETSQLDATASET(
        'SELECT SERIES, CODE, NAME, TFPRMS, FPRMS, ISACTIVE FROM SERIES WHERE COMPANY=:1 AND SOSOURCE=:2 ORDER BY CODE', co, sosource);
    out.push('Series: ' + s.RECORDCOUNT);
    s.FIRST;
    while (!s.EOF) {
        out.push('  SERIES ' + s.SERIES + ' ' + s.CODE + ' | ' + s.NAME + ' | TFPRMS ' + s.TFPRMS + ' FPRMS ' + s.FPRMS + ' active ' + s.ISACTIVE);
        s.NEXT;
    }
    var d = X.GETSQLDATASET(
        'SELECT TOP 5 F.FINDOC, F.TRNDATE, F.SERIES, F.FINCODE, F.TRDR, T.CODE AS TRDRCODE, T.NAME, F.NETAMNT, F.VATAMNT, F.SUMAMNT ' +
        'FROM FINDOC F LEFT JOIN TRDR T ON T.TRDR=F.TRDR ' +
        'WHERE F.COMPANY=:1 AND F.SOSOURCE=:2 ORDER BY F.FINDOC DESC', co, sosource);
    out.push('Latest docs: ' + d.RECORDCOUNT);
    d.FIRST;
    var first = 0;
    while (!d.EOF) {
        if (!first) first = parseInt(d.FINDOC, 10);
        out.push('  FINDOC ' + d.FINDOC + ' ' + String(d.TRNDATE).substring(0, 15) + ' series ' + d.SERIES + ' ' + d.FINCODE +
            ' | ' + d.TRDRCODE + ' ' + d.NAME + ' | ' + d.NETAMNT + ' / ' + d.VATAMNT + ' / ' + d.SUMAMNT);
        d.NEXT;
    }
    if (!first) return out.join('\n');

    out.push('Line tables of FINDOC ' + first + ':');
    var t = X.GETSQLDATASET(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME='FINDOC' AND TABLE_NAME<>'FINDOC' ORDER BY TABLE_NAME");
    t.FIRST;
    var lineTables = [];
    while (!t.EOF) {
        var tn = String(t.TABLE_NAME);
        try {
            var n = parseInt(X.SQL('SELECT COUNT(*) FROM ' + tn + ' WHERE FINDOC=:1', first), 10);
            if (n > 0) { out.push('  ' + tn + ': ' + n + ' row(s)'); lineTables.push(tn); }
        } catch (e) { }
        t.NEXT;
    }
    for (var i = 0; i < lineTables.length; i++) {
        var tn2 = lineTables[i];
        if (tn2 == 'FINDOC' ) continue;
        try {
            var r = X.GETSQLDATASET('SELECT TOP 1 * FROM ' + tn2 + ' WHERE FINDOC=:1', first);
            var js = String(r.JSON);
            out.push('  ' + tn2 + ' first row: ' + (js.length > 1500 ? js.substring(0, 1500) + ' ...' : js));
        } catch (e) { out.push('  ' + tn2 + ': ' + e.message); }
    }

    var objs = ['CREDSPECIAL', 'CRDSPECIAL', 'CREDITORSPECIAL', 'SPECIALCRED', 'SUPSPECIAL', 'EXPDOC', 'PURDOC', 'GENDOC'];
    for (var k = 0; k < objs.length; k++) {
        try {
            var o = X.CREATEOBJFORM(objs[k]);
            try {
                o.DBLOCATE(first);
                var fc = String(o.FindTable('FINDOC').FINCODE);
                var tabs = [], cand = ['ITELINES', 'SRVLINES', 'EXPLINES', 'MTRLINES', 'RECLINES', 'EXPANAL', 'CCCLINES', 'VATANAL'];
                for (var m = 0; m < cand.length; m++) {
                    try { var tb = o.FindTable(cand[m]); if (tb) tabs.push(cand[m] + '(' + tb.RECORDCOUNT + ')'); } catch (e2) { }
                }
                out.push('Object ' + objs[k] + ': located, FINCODE ' + fc + ', tables ' + tabs.join(' '));
            } finally { o.FREE; }
        } catch (e) { out.push('Object ' + objs[k] + ': ' + e.message); }
    }
    return out.join('\n');
}

// ============================================================================
// EXPENSES  (Ειδικές πιστωτών: object LINCREDOC, SOSOURCE 1653, lines table LINLINES -> SQL MTRLINES)
//
// Same hybrid flow, separate files so purchases and expenses never mix:
//   C:\Soft1\DEVIN-EXP.txt     : date;series;creditor;docnum;account;netvalue[;vat][;comment]
//     series   : code 'ΤΙΜΔ' (SOSOURCE 1653)            | 'ID:1001'
//     creditor : creditor code '0113' | 'AFM:...' (TRDR SODTYPE 16) | 'ID:121627'
//     account  : expense account code as shown in the line "Κωδικός" (MTRL SODTYPE 53) | 'ID:118218'
//     netvalue : line net value (Αξία), e.g. '1127,90'  (qty is always 1, no price)
//     vat      : percentage, default 24 | 'ID:1410'
//     comment  : optional line "Αιτιολογία"
//   DevinExpMakeHead  -> C:\Soft1\DEVIN-EXPHEAD.txt : date;series;trdr;fincode;mtrl;netvalue;vat;comment;year;month (ISO-8859-7)
//   ASCII Import wizard on list "Ειδικές πιστωτών", definition mapping:
//     LINCREDOC.TRNDATE=imp(1)  LINCREDOC.SERIES=imp(2)  LINCREDOC.TRDR=imp(3)  LINCREDOC.FINCODE=imp(4)
//     LINLINES.MTRL=imp(5)      LINLINES.LINEVAL=imp(6)  LINLINES.VAT=imp(7)    LINLINES.COMMENTS=imp(8)
//   DevinExpAddLines  -> appends lines 2..n via LINCREDOC/LINLINES (SKIP when complete)
// ============================================================================

function DevinExpSeries(s) {
    s = String(s).replace(/^\s+|\s+$/g, '');
    if (/^ID:/i.test(s)) return parseInt(s.substring(3), 10);
    return DevinOne('SELECT SERIES AS ID FROM SERIES WHERE COMPANY=:1 AND SOSOURCE=1653 AND CODE=:2', [X.SYS.COMPANY, s], 'Expense series');
}

function DevinCreditor(s) {
    s = String(s).replace(/^\s+|\s+$/g, '');
    if (/^ID:/i.test(s)) return parseInt(s.substring(3), 10);
    if (/^AFM:/i.test(s))
        return DevinOne('SELECT TRDR AS ID FROM TRDR WHERE COMPANY=:1 AND SODTYPE=16 AND ISACTIVE=1 AND AFM=:2', [X.SYS.COMPANY, s.substring(4)], 'Creditor AFM');
    return DevinOne('SELECT TRDR AS ID FROM TRDR WHERE COMPANY=:1 AND SODTYPE=16 AND CODE=:2', [X.SYS.COMPANY, s], 'Creditor code');
}

function DevinExpAcct(s) {
    s = String(s).replace(/^\s+|\s+$/g, '');
    if (/^ID:/i.test(s)) return parseInt(s.substring(3), 10);
    return DevinOne('SELECT MTRL AS ID FROM MTRL WHERE COMPANY=:1 AND SODTYPE=53 AND CODE=:2', [X.SYS.COMPANY, s], 'Expense account code');
}

function DevinExpReadRows(fileName) {
    var rows = [];
    var f = X.EXEC('CODE:PILib.OpenText', fileName, 65001);
    try {
        while (!X.EXEC('CODE:PILib.EOF', f)) {
            var line = String(X.EXEC('CODE:PILib.ReadLine', f)).replace(/^\uFEFF/, '');
            if (line.replace(/\s/g, '') == '') continue;
            var p = line.split(';');
            if (p.length < 6) throw new Error('Bad line (need 6+ fields): ' + line);
            rows.push({
                trndate: p[0], series: DevinExpSeries(p[1]), trdr: DevinCreditor(p[2]),
                docnum: p[3].replace(/^\s+|\s+$/g, ''),
                sosource: 1653, mtrl: DevinExpAcct(p[4]), val: DevinNum(p[5]),
                vat: DevinVat(p.length > 6 ? p[6] : ''),
                comment: p.length > 7 ? p.slice(7).join(';') : ''
            });
        }
    }
    finally {
        X.EXEC('CODE:PILib.CloseText', f);
    }
    return rows;
}

function DevinExpMakeHead(fileName) {
    if (!fileName) fileName = 'C:\\Soft1\\DEVIN-EXP.txt';
    var headName = fileName.replace(/DEVIN-EXP\.txt$/i, 'DEVIN-EXPHEAD.txt');
    if (headName == fileName) headName = fileName + '.head.txt';
    var docs = DevinGroup(DevinExpReadRows(fileName));
    var out = [], log = [];
    for (var i = 0; i < docs.length; i++) {
        var L = docs[i].lines[0], d = docs[i], fincode = DevinFincode(d);
        var n = parseInt(X.SQL(
            'SELECT COUNT(*) FROM FINDOC WHERE COMPANY=:1 AND SOSOURCE=1653 AND TRDR=:2 AND FINCODE=:3',
            X.SYS.COMPANY, d.trdr, fincode), 10);
        if (n > 0) { log.push('SKIP ' + fincode + ' (already exists, not written to HEAD)'); continue; }
        var dp = String(d.trndate).split('/');   // dd/mm/yyyy -> FISCPRD (year), PERIOD (month)
        if (dp.length != 3) throw new Error('Bad date (need dd/mm/yyyy): ' + d.trndate);
        var row = [d.trndate, d.series, d.trdr, fincode, L.mtrl,
            String(L.val).replace('.', ','), L.vat, String(L.comment).replace(/;/g, ','),
            dp[2], parseInt(dp[1], 10)].join(';');
        out.push(row);
        log.push('HEAD ' + row);
    }
    var f = X.EXEC('CODE:PILib.CreateText', headName, 28597);
    try {
        for (var j = 0; j < out.length; j++) X.CALLPUBLISHED('PILib.WriteLine', f, out[j]);
    }
    finally {
        X.EXEC('CODE:PILib.CloseText', f);
    }
    return 'Wrote ' + out.length + ' of ' + docs.length + ' header row(s) to ' + headName +
        (out.length == 0 ? '\nNothing new - do NOT run the wizard.' : '\nRun the wizard (Ειδικές πιστωτών) with this file, then DevinExpAddLines.') +
        '\n' + log.join('\n');
}

function DevinExpAddLines(fileName) {
    if (!fileName) fileName = 'C:\\Soft1\\DEVIN-EXP.txt';
    var docs = DevinGroup(DevinExpReadRows(fileName));
    var out = ['File: ' + fileName, 'Docs in file: ' + docs.length];
    for (var i = 0; i < docs.length; i++) {
        var d = docs[i], fincode = DevinFincode(d);
        try {
            var ds = X.GETSQLDATASET(
                'SELECT FINDOC FROM FINDOC WHERE COMPANY=:1 AND SOSOURCE=1653 AND TRDR=:2 AND FINCODE=:3 ORDER BY FINDOC',
                X.SYS.COMPANY, d.trdr, fincode);
            if (ds.RECORDCOUNT == 0) { out.push('ERR  ' + fincode + ': header not found (run the ASCII Import wizard first)'); continue; }
            if (ds.RECORDCOUNT > 1) { out.push('ERR  ' + fincode + ': ' + ds.RECORDCOUNT + ' documents with this code for the creditor - check manually'); continue; }
            var id = parseInt(ds.FINDOC, 10);
            var have = parseInt(X.SQL('SELECT COUNT(*) FROM MTRLINES WHERE FINDOC=:1', id), 10);
            if (have >= d.lines.length) { out.push('SKIP ' + fincode + ' -> FINDOC ' + id + ' (already ' + have + ' lines)'); continue; }
            if (have != 1) { out.push('ERR  ' + fincode + ' -> FINDOC ' + id + ': has ' + have + ' lines, expected 1 - check manually'); continue; }
            var firstMtrl = parseInt(X.SQL('SELECT MTRL FROM MTRLINES WHERE FINDOC=:1', id), 10);
            if (firstMtrl != d.lines[0].mtrl) { out.push('ERR  ' + fincode + ' -> FINDOC ' + id + ': first line account ' + firstMtrl + ' <> file ' + d.lines[0].mtrl); continue; }

            var obj = X.CREATEOBJFORM('LINCREDOC');
            try {
                obj.DBLOCATE(id);
                var lns = obj.FindTable('LINLINES');
                for (var j = 1; j < d.lines.length; j++) {
                    var L = d.lines[j];
                    lns.Append;
                    lns.MTRL = L.mtrl;
                    lns.LINEVAL = L.val;
                    lns.VAT = L.vat;
                    if (L.comment) lns.COMMENTS = L.comment;
                    lns.Post;
                }
                var r = obj.DBPOST;
                if (!r) throw new Error(String(obj.GETLASTERROR));
            }
            finally {
                obj.FREE;
            }
            var now = X.GETSQLDATASET(
                'SELECT FINCODE, (SELECT COUNT(*) FROM MTRLINES M WHERE M.FINDOC=F.FINDOC) AS LINES, NETAMNT, VATAMNT, SUMAMNT FROM FINDOC F WHERE FINDOC=:1', id);
            out.push('OK   ' + fincode + ' -> FINDOC ' + id + ': added ' + (d.lines.length - 1) + ' line(s), now ' + now.JSON);
        }
        catch (e) {
            out.push('ERR  ' + fincode + ': ' + e.message);
        }
    }
    return out.join('\n');
}

// Read-only: header + lines of existing expense documents (SOSOURCE 1653) with this FINCODE, in txt codes.
// Argument: a FINCODE (e.g. 'ΤΙΜΔ-00788') or 'AFM:999082935' for the 5 latest documents of that creditor.
function DevinExpShowEnartia() { return DevinExpShowDoc('AFM:999082935'); }
// FEDEX, ΚΑΡΑΣΟΥΛΗΣ, COGNITION/CARVECO: how they were booked historically (series, account, vat, payment).
function DevinExpShowNext() {
    return [DevinExpShowDoc('AFM:095283423'), DevinExpShowDoc('AFM:094453479'), DevinExpShowDoc('AFM:307946483')].join('\n\n');
}

function DevinExpShowDoc(fincode) {
    if (!fincode) fincode = 'ΤΙΜΔ-00788';
    var out = ['FINCODE ' + fincode];
    var byAfm = /^AFM:/i.test(fincode);
    var h = X.GETSQLDATASET(
        'SELECT ' + (byAfm ? 'TOP 5 ' : '') + 'F.FINDOC, F.TRNDATE, S.CODE AS SERIESCODE, T.CODE AS TRDRCODE, T.NAME, T.AFM, F.PAYMENT, F.NETAMNT, F.VATAMNT, F.SUMAMNT, F.FINCODE ' +
        'FROM FINDOC F JOIN SERIES S ON S.SERIES=F.SERIES AND S.COMPANY=F.COMPANY AND S.SOSOURCE=F.SOSOURCE JOIN TRDR T ON T.TRDR=F.TRDR AND T.COMPANY=F.COMPANY AND T.SODTYPE=16 ' +
        'WHERE F.COMPANY=:1 AND F.SOSOURCE=1653 AND ' + (byAfm ? 'T.AFM=:2 ORDER BY F.FINDOC DESC' : 'F.FINCODE=:2 ORDER BY F.FINDOC'),
        X.SYS.COMPANY, byAfm ? fincode.substring(4) : fincode);
    out.push('Documents: ' + h.RECORDCOUNT);
    h.FIRST;
    while (!h.EOF) {
        out.push('--- FINDOC ' + h.FINDOC + '  ' + h.FINCODE + '  ' + h.TRNDATE + '  ' + h.SERIESCODE + '  creditor ' + h.TRDRCODE + ' ' + h.NAME +
            ' (AFM ' + h.AFM + ')  payment ' + h.PAYMENT + '  net ' + h.NETAMNT + ' vat ' + h.VATAMNT + ' total ' + h.SUMAMNT);
        var l = X.GETSQLDATASET(
            'SELECT L.LINENUM, M.CODE, M.NAME, L.QTY1, L.LINEVAL, L.VATAMNT, V.PERCNT, L.VAT, V.NAME AS VATNAME, L.COMMENTS ' +
            'FROM MTRLINES L JOIN MTRL M ON M.MTRL=L.MTRL LEFT JOIN VAT V ON V.VAT=L.VAT ' +
            'WHERE L.FINDOC=:1 ORDER BY L.LINENUM', h.FINDOC);
        l.FIRST;
        while (!l.EOF) {
            out.push('    ' + l.CODE + ' | ' + l.NAME + ' | qty ' + l.QTY1 + ' | value ' + l.LINEVAL + ' | vat% ' + l.PERCNT + ' (VAT id ' + l.VAT + ' ' + l.VATNAME + ') | ' + l.COMMENTS);
            l.NEXT;
        }
        h.NEXT;
    }
    return out.join('\n');
}

// ============================================================================
// ONE-STEP IMPORT (no ASCII wizard, no HEAD files)
//
// DevinImportAll(fileName, dryRun)     : DEVIN-IMPORT.txt -> new PURDOC documents (header + ALL lines)
// DevinExpImportAll(fileName, dryRun)  : DEVIN-EXP.txt    -> new LINCREDOC documents (header + ALL lines)
// DevinDryRun()                        : both files, nothing is saved - shows what SoftOne WOULD create
// DevinProbeInsert(objName)            : read-only, lists header fields/defaults after DBINSERT, then DBCANCEL
//
// Per document: SKIP if supplier+FINCODE already exists (any line count), otherwise
//   DBINSERT -> header (SERIES, TRNDATE, TRDR, FINCODE) -> Append every line -> compare the totals
//   SoftOne computed IN MEMORY with the txt (net +-0.02) -> DBPOST, or DBCANCEL + ERR on any mismatch/error.
// Same object model as DevinAddLines (SoftOne business objects, all validations apply); no SQL writes.
// The old flow (MakeHead -> wizard -> AddLines) stays available as fallback.
// ============================================================================

// Editor parameters arrive as strings: '', '0', 'false' -> false; 1, '1', true -> true
function DevinFlag(v) {
    if (v === true || v === 1) return true;
    var s = String(v == null ? '' : v).replace(/^\s+|\s+$/g, '').toLowerCase();
    return s == '1' || s == 'true' || s == 'yes';
}

function DevinRound2(x) {
    return Math.round(x * 100) / 100;
}

function DevinDateParts(s) {
    var dp = String(s).replace(/^\s+|\s+$/g, '').split('/');
    if (dp.length != 3) throw new Error('Bad date (need dd/mm/yyyy): ' + s);
    return { d: parseInt(dp[0], 10), m: parseInt(dp[1], 10), y: parseInt(dp[2], 10) };
}

// Assigns a date field, trying a JS Date first (COM VT_DATE) and the dd/mm/yyyy string as fallback;
// verifies the value read back contains the expected day/month/year.
function DevinSetDate(tbl, field, s) {
    var p = DevinDateParts(s), ok = false, err = '';
    var attempts = [new Date(p.y, p.m - 1, p.d), s];
    for (var i = 0; i < attempts.length && !ok; i++) {
        try {
            tbl[field] = attempts[i];
            var raw = tbl[field], back = String(raw);
            var bd = (raw && typeof raw.getTime == 'function') ? raw : new Date(back);
            if (!isNaN(bd.getTime())) {
                ok = bd.getFullYear() == p.y && bd.getMonth() == p.m - 1 && bd.getDate() == p.d;
            } else {
                var dd = ('0' + p.d).slice(-2), mm = ('0' + p.m).slice(-2);
                ok = back.indexOf(String(p.y)) >= 0 &&
                    (back.indexOf(dd + '/' + mm) >= 0 || back.indexOf(dd + '-' + mm) >= 0 ||
                     back.indexOf(mm + '/' + dd) >= 0 || back.indexOf(p.y + '-' + mm + '-' + dd) >= 0 ||
                     back.indexOf(p.y + '/' + mm + '/' + dd) >= 0);
            }
            if (!ok) err = 'read back ' + back;
        } catch (e) { err = e.message; }
    }
    if (!ok) throw new Error(field + ' = ' + s + ' not accepted (' + err + ')');
}

function DevinTxtNet(d, spec) {
    var net = 0;
    for (var j = 0; j < d.lines.length; j++) net += spec.lineNet(d.lines[j]);
    return DevinRound2(net);
}

// FINDOC id of the document DBPOST just created, when the object does not report it:
// the single new row for this creditor/supplier above the id seen before posting.
function DevinNewDocId(spec, d, maxBefore) {
    var ds = X.GETSQLDATASET(
        'SELECT FINDOC, FINCODE FROM FINDOC WHERE COMPANY=:1 AND SOSOURCE=' + spec.sosource + ' AND TRDR=:2 AND FINDOC>:3 ORDER BY FINDOC',
        X.SYS.COMPANY, d.trdr, maxBefore);
    if (ds.RECORDCOUNT != 1)
        throw new Error('saved, but found ' + ds.RECORDCOUNT + ' new documents for this trdr afterwards (expected 1) - check manually');
    return parseInt(ds.FINDOC, 10);
}

function DevinDocRow(findoc) {
    var chk = X.GETSQLDATASET(
        'SELECT FINDOC, FINCODE, FISCPRD, PERIOD, TRNDATE, NETAMNT, VATAMNT, SUMAMNT, ' +
        '(SELECT COUNT(*) FROM MTRLINES M WHERE M.FINDOC=F.FINDOC) AS LINES FROM FINDOC F WHERE FINDOC=:1', findoc);
    if (chk.RECORDCOUNT != 1) throw new Error('FINDOC ' + findoc + ' not found after save - check manually');
    return chk;
}

// Re-open a saved document and set its number (same DBLOCATE -> change -> DBPOST path as AddLines).
function DevinRenumber(spec, findoc, fincode) {
    var obj = X.CREATEOBJFORM(spec.objName), posted = false;
    try {
        obj.DBLOCATE(findoc);
        obj.FindTable('FINDOC').FINCODE = fincode;
        var r = obj.DBPOST;
        if (!r) throw new Error('renumber: ' + String(obj.GETLASTERROR));
        posted = true;
    } finally {
        if (!posted) { try { obj.DBCANCEL; } catch (e0) { } }
        obj.FREE;
    }
}

// spec: { objName, sosource, linesTable, fillLine(lns, L), lineNet(L), what }
function DevinCreateDocs(docs, spec, dryRun) {
    var out = [(dryRun ? 'DRY RUN (nothing saved) - ' : '') + spec.what + ': ' + docs.length + ' document(s) in file'];
    var made = 0, skipped = 0, errors = 0;
    for (var i = 0; i < docs.length; i++) {
        var d = docs[i], fincode = '?';
        try {
            fincode = DevinFincode(d);
            var ex = X.GETSQLDATASET(
                'SELECT FINDOC, (SELECT COUNT(*) FROM MTRLINES M WHERE M.FINDOC=F.FINDOC) AS LINES FROM FINDOC F ' +
                'WHERE COMPANY=:1 AND SOSOURCE=' + spec.sosource + ' AND TRDR=:2 AND FINCODE=:3 ORDER BY FINDOC',
                X.SYS.COMPANY, d.trdr, fincode);
            if (ex.RECORDCOUNT > 0) {
                var have = parseInt(ex.LINES, 10);
                out.push('SKIP ' + fincode + ' -> FINDOC ' + ex.FINDOC + ' already exists (' + have + ' of ' + d.lines.length + ' lines' +
                    (ex.RECORDCOUNT > 1 ? ', ' + ex.RECORDCOUNT + ' documents!' : '') +
                    (have < d.lines.length ? ' - incomplete, run ' + spec.addLines : '') + ')');
                skipped++;
                continue;
            }
            var wantNet = DevinTxtNet(d, spec);
            var obj = X.CREATEOBJFORM(spec.objName), posted = false;
            try {
                obj.DBINSERT;
                var hdr = obj.FindTable('FINDOC');
                hdr.SERIES = d.series;
                DevinSetDate(hdr, 'TRNDATE', d.trndate);
                hdr.TRDR = d.trdr;
                hdr.FINCODE = fincode;
                var lns = obj.FindTable(spec.linesTable);
                for (var j = 0; j < d.lines.length; j++) {
                    lns.Append;
                    spec.fillLine(lns, d.lines[j]);
                    lns.Post;
                }
                var gotNet = DevinNum(hdr.NETAMNT), gotVat = DevinNum(hdr.VATAMNT), gotSum = DevinNum(hdr.SUMAMNT);
                var gotLines = parseInt(lns.RECORDCOUNT, 10);
                var gotSeries = parseInt(hdr.SERIES, 10), gotTrdr = parseInt(hdr.TRDR, 10), gotCode = String(hdr.FINCODE);
                var problems = [];
                if (gotLines != d.lines.length) problems.push('lines ' + gotLines + ' <> ' + d.lines.length);
                if (Math.abs(gotNet - wantNet) > 0.02)
                    problems.push('net ' + gotNet + ' <> txt ' + wantNet + (gotNet == 0 && gotLines > 0 ? ' (object did not compute totals in memory)' : ''));
                if (gotSeries != d.series) problems.push('series ' + gotSeries + ' <> ' + d.series);
                if (gotTrdr != d.trdr) problems.push('trdr ' + gotTrdr + ' <> ' + d.trdr);
                if (gotCode != fincode) problems.push('fincode ' + gotCode + ' <> ' + fincode);
            } catch (eInner) {
                try { obj.DBCANCEL; } catch (e0) { }
                obj.FREE;
                throw eInner;
            }
            // (kept outside the inner try so a DBCANCEL failure is reported separately)
            var line = fincode + ' ' + d.trndate + ' lines ' + gotLines + ' net ' + gotNet + ' vat ' + gotVat + ' total ' + gotSum;
            if (problems.length) {
                try { obj.DBCANCEL; } finally { obj.FREE; }
                out.push('ERR  ' + line + ' -> NOT saved: ' + problems.join('; '));
                errors++;
                continue;
            }
            if (dryRun) {
                try { obj.DBCANCEL; } finally { obj.FREE; }
                out.push('DRY  ' + line + ' -> would be created');
                made++;
                continue;
            }
            var maxBefore = parseInt(X.SQL('SELECT ISNULL(MAX(FINDOC), 0) FROM FINDOC WHERE COMPANY=:1 AND SOSOURCE=' + spec.sosource, X.SYS.COMPANY), 10) || 0;
            var newId = 0;
            try {
                var r = obj.DBPOST;
                if (!r) throw new Error(String(obj.GETLASTERROR));
                posted = true;
                try { newId = parseInt(hdr.FINDOC, 10) || 0; } catch (e2) { }
            } finally {
                if (!posted) { try { obj.DBCANCEL; } catch (e1) { } }
                obj.FREE;
            }
            if (!newId) newId = DevinNewDocId(spec, d, maxBefore);
            var chk = DevinDocRow(newId);
            var note = '';
            if (String(chk.FINCODE) != fincode) {
                // AUTONUMBER series: DBPOST of a new document replaces FINCODE with the next series number.
                // Editing the saved document does not renumber, so write the supplier's number now.
                var got = String(chk.FINCODE), why = '';
                try { DevinRenumber(spec, newId, fincode); } catch (eR) { why = ': ' + eR.message; }
                chk = DevinDocRow(newId);
                if (String(chk.FINCODE) != fincode)
                    throw new Error('SAVED as FINDOC ' + newId + ' with number "' + chk.FINCODE + '" but the number could NOT be changed to ' +
                        fincode + why + ' - delete FINDOC ' + newId + ' (number ' + chk.FINCODE + ') manually before running again');
                note = '  (numbered ' + got + ' by SoftOne, renamed to ' + fincode + ')';
            }
            var p = DevinDateParts(d.trndate), warn = '';
            if (parseInt(chk.FISCPRD, 10) != p.y || parseInt(chk.PERIOD, 10) != p.m)
                warn = '  WARNING period ' + chk.FISCPRD + '/' + chk.PERIOD + ' <> date ' + d.trndate;
            out.push('OK   ' + fincode + ' -> FINDOC ' + newId + ': lines ' + chk.LINES + ' net ' + chk.NETAMNT +
                ' vat ' + chk.VATAMNT + ' total ' + chk.SUMAMNT + warn + note);
            made++;
        }
        catch (e) {
            out.push('ERR  ' + fincode + ': ' + e.message);
            errors++;
        }
    }
    out.push((dryRun ? 'Would create ' : 'Created ') + made + ', skipped ' + skipped + ', errors ' + errors);
    return out.join('\n');
}

function DevinPurSpec() { return {
    what: 'Purchases (PURDOC)', objName: 'PURDOC', sosource: 1251, linesTable: 'ITELINES', addLines: 'DevinAddLines',
    fillLine: function (lns, L) {
        lns.MTRL = L.mtrl;
        lns.QTY1 = L.qty;
        lns.PRICE = L.price;
        lns.VAT = L.vat;
        if (L.disc) lns.DISC1PRC = L.disc;
        lns.WHOUSE = 1000;
    },
    lineNet: function (L) { return DevinRound2(L.qty * L.price * (1 - (L.disc || 0) / 100)); }
}; }

function DevinExpSpec() { return {
    what: 'Expenses (LINCREDOC)', objName: 'LINCREDOC', sosource: 1653, linesTable: 'LINLINES', addLines: 'DevinExpAddLines',
    fillLine: function (lns, L) {
        lns.MTRL = L.mtrl;
        lns.LINEVAL = L.val;
        lns.VAT = L.vat;
        if (L.comment) lns.COMMENTS = L.comment;
    },
    lineNet: function (L) { return L.val; }
}; }

function DevinImportAll(fileName, dryRun) {
    if (!fileName) fileName = 'C:\\Soft1\\DEVIN-IMPORT.txt';
    return 'File: ' + fileName + '\n' + DevinCreateDocs(DevinGroup(DevinReadRows(fileName)), DevinPurSpec(), DevinFlag(dryRun));
}

function DevinExpImportAll(fileName, dryRun) {
    if (!fileName) fileName = 'C:\\Soft1\\DEVIN-EXP.txt';
    return 'File: ' + fileName + '\n' + DevinCreateDocs(DevinGroup(DevinExpReadRows(fileName)), DevinExpSpec(), DevinFlag(dryRun));
}

// '' when the file opens, otherwise the reason (used only to skip missing files in DevinAll)
function DevinFileProblem(fileName) {
    try { var f = X.EXEC('CODE:PILib.OpenText', fileName, 65001); X.EXEC('CODE:PILib.CloseText', f); return ''; }
    catch (e) { return e.message; }
}

// Everything the .exe produced, in one call. dryRun=1 -> DevinDryRun.
function DevinAll(dryRun) {
    var out = [], files = [['C:\\Soft1\\DEVIN-EXP.txt', DevinExpImportAll], ['C:\\Soft1\\DEVIN-IMPORT.txt', DevinImportAll]];
    for (var i = 0; i < files.length; i++) {
        var problem = DevinFileProblem(files[i][0]);
        if (problem) { out.push('File: ' + files[i][0] + ' - cannot open (' + problem + '), nothing to do'); continue; }
        try { out.push(files[i][1](files[i][0], dryRun)); }
        catch (e) { out.push('File: ' + files[i][0] + '\nERR  ' + e.message); }
    }
    return out.join('\n\n');
}

function DevinDryRun() { return DevinAll(1); }

// Read-only: the n latest documents of a source (default: expenses 1653) with FINCODE/comments,
// followed by every column of the SERIES row of the latest one (numbering settings).
function DevinShowLast(sosource, n, seriesCode) {
    sosource = parseInt(sosource, 10) || 1653; n = parseInt(n, 10) || 5; if (!seriesCode) seriesCode = 'ΤΔΕΕ';
    var out = ['Latest ' + n + ' documents, SOSOURCE ' + sosource + ', company ' + X.SYS.COMPANY];
    var h = X.GETSQLDATASET(
        'SELECT TOP ' + n + ' F.FINDOC, F.FINCODE, F.SERIES, S.CODE AS SERIESCODE, T.CODE AS TRDRCODE, F.TRNDATE, ' +
        'F.NETAMNT, F.SUMAMNT, F.PAYMENT, F.COMMENTS, F.INSDATE, F.FISCPRD, F.PERIOD ' +
        'FROM FINDOC F LEFT JOIN SERIES S ON S.SERIES=F.SERIES AND S.COMPANY=F.COMPANY AND S.SOSOURCE=F.SOSOURCE ' +
        'LEFT JOIN TRDR T ON T.TRDR=F.TRDR AND T.COMPANY=F.COMPANY AND T.SODTYPE=16 ' +
        'WHERE F.COMPANY=:1 AND F.SOSOURCE=' + sosource + ' ORDER BY F.FINDOC DESC', X.SYS.COMPANY);
    h.FIRST;
    while (!h.EOF) {
        out.push('FINDOC ' + h.FINDOC + ' | FINCODE "' + h.FINCODE + '" | series ' + h.SERIESCODE + ' (' + h.SERIES + ')' +
            ' | trdr ' + h.TRDRCODE + ' | ' + h.TRNDATE + ' | net ' + h.NETAMNT + ' total ' + h.SUMAMNT + ' | payment ' + h.PAYMENT +
            ' | ' + h.FISCPRD + '/' + h.PERIOD + ' | ins ' + h.INSDATE + ' | comments "' + h.COMMENTS + '"');
        var l = X.GETSQLDATASET('SELECT L.LINENUM, M.CODE, L.LINEVAL, L.VAT, L.COMMENTS FROM MTRLINES L JOIN MTRL M ON M.MTRL=L.MTRL WHERE L.FINDOC=:1 ORDER BY L.LINENUM', h.FINDOC);
        l.FIRST;
        while (!l.EOF) { out.push('    line ' + l.LINENUM + ' ' + l.CODE + ' value ' + l.LINEVAL + ' vat ' + l.VAT + ' "' + l.COMMENTS + '"'); l.NEXT; }
        h.NEXT;
    }
    var codes = [seriesCode, 'ΤΙΜΔ'];
    for (var k = 0; k < codes.length; k++) {
        var sid = 0;
        try { sid = DevinOne('SELECT SERIES AS ID FROM SERIES WHERE COMPANY=:1 AND SOSOURCE=' + sosource + ' AND CODE=:2', [X.SYS.COMPANY, codes[k]], 'Series'); }
        catch (eS) { out.push('', 'SERIES ' + codes[k] + ': ' + eS.message); continue; }
        out.push('', 'SERIES ' + codes[k] + ' (' + sid + ') settings:');
        var cols = X.GETSQLDATASET("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='SERIES' ORDER BY ORDINAL_POSITION");
        cols.FIRST;
        while (!cols.EOF) {
            var c = String(cols.COLUMN_NAME), v = '';
            try { v = String(X.SQL('SELECT CAST(' + c + ' AS NVARCHAR(200)) FROM SERIES WHERE COMPANY=:1 AND SOSOURCE=' + sosource + ' AND SERIES=:2', X.SYS.COMPANY, sid)); } catch (e) { v = '?' + e.message; }
            if (v != '' && v != 'null' && v != 'undefined' && v != '0') out.push('  ' + c + ' = ' + v);
            cols.NEXT;
        }
    }
    return out.join('\n');
}

// Read-only: DBINSERT on the object, show header defaults + which tables exist, then DBCANCEL.
function DevinProbeInsert(objName) {
    if (!objName) objName = 'PURDOC';
    var out = ['Object ' + objName], obj = X.CREATEOBJFORM(objName);
    try {
        try { obj.DBINSERT; out.push('DBINSERT: ok'); }
        catch (e) { out.push('DBINSERT: ' + e.message); return out.join('\n'); }
        var hdr = obj.FindTable('FINDOC');
        var flds = ['FINDOC', 'COMPANY', 'SOSOURCE', 'SERIES', 'TRNDATE', 'FISCPRD', 'PERIOD', 'TRDR', 'FINCODE', 'PAYMENT', 'WHOUSE', 'NETAMNT', 'VATAMNT', 'SUMAMNT', 'TRDBRANCH', 'ISCANCEL'];
        for (var i = 0; i < flds.length; i++) {
            try { out.push('  FINDOC.' + flds[i] + ' = ' + hdr[flds[i]]); } catch (e2) { out.push('  FINDOC.' + flds[i] + ': ' + e2.message); }
        }
        try { hdr.SERIES = objName == 'PURDOC' ? DevinSeries('ΤΔΑ') : DevinExpSeries('ΤΙΜΔ'); out.push('  after SERIES: TRNDATE ' + hdr.TRNDATE + ' PAYMENT ' + hdr.PAYMENT + ' WHOUSE ' + hdr.WHOUSE); } catch (e3) { out.push('  set SERIES: ' + e3.message); }
        try { DevinSetDate(hdr, 'TRNDATE', '15/09/2026'); out.push('  set TRNDATE 15/09/2026 -> ' + hdr.TRNDATE + ' FISCPRD ' + hdr.FISCPRD + ' PERIOD ' + hdr.PERIOD); } catch (e4) { out.push('  set TRNDATE: ' + e4.message); }
        var cand = ['ITELINES', 'LINLINES', 'SRVLINES', 'EXPLINES', 'MTRLINES', 'VATANAL'];
        for (var m = 0; m < cand.length; m++) {
            try { var tb = obj.FindTable(cand[m]); if (tb) out.push('  table ' + cand[m] + ' (' + tb.RECORDCOUNT + ')'); } catch (e5) { }
        }
    }
    finally {
        try { obj.DBCANCEL; out.push('DBCANCEL: ok'); } catch (e6) { out.push('DBCANCEL: ' + e6.message); }
        obj.FREE;
    }
    return out.join('\n');
}
