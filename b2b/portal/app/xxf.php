<?php
declare(strict_types=1);

// XXF (SoftOne import) — PHP port του b2b/xxf/xsf_ref.py + mk_ref.py
// (ίδιος αλγόριθμος, αναλυτικά στο b2b/xxf/README.md).
//
// Format: bytes 0..0x1b header (ως έχει), μετά groups:
//   u8 namelen + name + u32 tablecount + ανά πίνακα: u32 bloblen + blob.
//   blob: 'XSF_' + u32 + u8 namelen + name + u32 hdr + u16 fieldcount
//         + ανά πεδίο 4×u16 (type,size,off,attr) + name\0.
//   μετά ανά γραμμή: 0x00 + u32 rowindex + ανά πεδίο len-prefixed value
//   (L byte; 0 = NULL; 0xFE → u16 len; 0xFF → u32 len; μετά L raw bytes).
//   types: 3/1027 int32 LE, 2 int16 LE, 6 double LE,
//          11 datetime = double ms (toordinal × 86400000 + ms of day,
//          τοπική ώρα Ελλάδας), 1/513 text cp1253.

function xxf_fields(string $blob): array
{
    $nlen = ord($blob[8]);
    $p = 9 + $nlen;
    $h = unpack('Vhdr/vcnt', $blob, $p);
    $p += 6;
    $fs = [];
    for ($i = 0; $i < $h['cnt']; $i++) {
        $f = unpack('vtype/vsize/voff/vattr', $blob, $p);
        $p += 8;
        $e = strpos($blob, "\0", $p);
        $f['name'] = substr($blob, $p, $e - $p);
        $p = $e + 1;
        $fs[] = $f;
    }
    return [$fs, $p];
}

// Γραμμές ως map field → ΑΜΕΤΑΒΛΗΤΟ raw segment (len-prefix + bytes).
function xxf_rows(string $blob, array $fs, int $p): array
{
    $R = [];
    $q = $p;
    $bl = strlen($blob);
    while ($q < $bl) {
        $q += 5;                                     // 0x00 + u32 row index
        $row = [];
        foreach ($fs as $f) {
            $s = $q;
            $L = ord($blob[$q]);
            $q++;
            if ($L === 0xFE) {
                $L = unpack('v', $blob, $q)[1];
                $q += 2;
            } elseif ($L === 0xFF) {
                $L = unpack('V', $blob, $q)[1];
                $q += 4;
            }
            $q += $L;
            $row[$f['name']] = substr($blob, $s, $q - $s);
        }
        $R[] = $row;
    }
    return $R;
}

function xxf_cp1253(string $s): string
{
    if (preg_match('/[^\x00-\x7F]/', $s) === 1) {
        $r = @iconv('UTF-8', 'CP1253', $s);
        if ($r === false) {
            throw new RuntimeException('XXF: μη cp1253 κείμενο');
        }
        return $r;
    }
    return $s;
}

function xxf_enc(int $t, $v): string
{
    if ($v === null) {
        return "\0";
    }
    if (is_float($v) || $t === 6 || $t === 11) {
        $raw = pack('e', (float)$v);
    } elseif ($t === 3 || $t === 1027) {
        $raw = pack('V', (int)$v);
    } elseif ($t === 2) {
        $raw = pack('v', (int)$v);
    } elseif (is_string($v)) {
        $raw = xxf_cp1253($v);
    } else {
        throw new RuntimeException('XXF: απροσδόκητη τιμή πεδίου');
    }
    $L = strlen($raw);
    if ($L < 0xFE) {
        return chr($L) . $raw;
    }
    if ($L < 0x10000) {
        return "\xFE" . pack('v', $L) . $raw;
    }
    return "\xFF" . pack('V', $L) . $raw;
}

function xxf_set(array &$row, array $types, string $name, $v): void
{
    if (!isset($types[$name])) {
        throw new RuntimeException("XXF: άγνωστο πεδίο $name");
    }
    $row[$name] = xxf_enc($types[$name], $v);
}

// 'Y-m-d' ή 'Y-m-d H:i:s' σε ώρα Ελλάδας → double ms (toordinal*86400000 + ms of day)
function xxf_dt(string $dt): float
{
    $fmt = strlen($dt) > 10 ? '!Y-m-d H:i:s' : '!Y-m-d';
    $d = DateTime::createFromFormat($fmt, $dt, new DateTimeZone('Europe/Athens'));
    if ($d === false) {
        throw new RuntimeException("XXF: κακή ημερομηνία $dt");
    }
    $days = intdiv(gmmktime(0, 0, 0, (int)$d->format('n'), (int)$d->format('j'),
                            (int)$d->format('Y')), 86400)
          + 719163;                                  // toordinal: 0001-01-01 = 1
    $ms = (int)$d->format('G') * 3600000
        + (int)$d->format('i') * 60000
        + (int)$d->format('s') * 1000;
    return $days * 86400000.0 + $ms;
}

function xxf_build(string $blob, array $fs, int $p, array $rows): string
{
    $out = substr($blob, 0, $p);
    $i = 1;
    foreach ($rows as $row) {
        $out .= "\x00" . pack('V', $i++);
        foreach ($fs as $f) {
            $out .= $row[$f['name']];
        }
    }
    return $out;
}

// $o = ['order_no', 'created_at' (Y-m-d H:i:s ώρα Ελλάδας)]
// $cust = ['id' (=TRDR), 'code', 'payment' (int|null)]
// $lines = ['item_id' (=MTRL), 'code', 'qty', 'price' (τελική χωρίς ΦΠΑ),
//           'net', 'vat', 'vat_code', 'mtrunit']
function order_xxf(array $o, array $cust, array $lines): string
{
    $tpl = @file_get_contents(__DIR__ . '/xxf_template_7021.XXF');
    if ($tpl === false) {
        throw new RuntimeException('XXF template missing');
    }

    // groups σε raw bytes (το όνομα μένει ως έχει)
    $p = 0x1c;
    $groups = [];
    $tl = strlen($tpl);
    while ($p < $tl) {
        $n = ord($tpl[$p]);
        $gname = substr($tpl, $p + 1, $n);
        $p += 1 + $n;
        $cnt = unpack('V', $tpl, $p)[1];
        $p += 4;
        $tabs = [];
        for ($i = 0; $i < $cnt; $i++) {
            $sz = unpack('V', $tpl, $p)[1];
            $blob = substr($tpl, $p + 4, $sz);
            $p += 4 + $sz;
            $tn = substr($blob, 0, 4) === 'XSF_' ? substr($blob, 9, ord($blob[8])) : '?';
            $tabs[] = [$tn, $blob];
        }
        $groups[] = [$gname, $tabs];
    }

    // σύνολα = ακριβώς τα net/vat της πύλης
    $net = $vat = $qty = 0.0;
    $vanal = [];                                   // vat_code => [net, vat]
    foreach ($lines as $l) {
        if (($l['vat_code'] ?? null) === null || ($l['mtrunit'] ?? null) === null) {
            throw new RuntimeException('XXF: λείπει vat_code/mtrunit για ' . (string)($l['code'] ?? '?'));
        }
        $net += (float)$l['net'];
        $vat += (float)$l['vat'];
        $qty += (float)$l['qty'];
        $vc = (int)$l['vat_code'];
        $vanal[$vc][0] = ($vanal[$vc][0] ?? 0.0) + (float)$l['net'];
        $vanal[$vc][1] = ($vanal[$vc][1] ?? 0.0) + (float)$l['vat'];
    }
    $net = round($net, 2);
    $vat = round($vat, 2);
    $tot = round($net + $vat, 2);

    $ordDt = (string)$o['created_at'];             // 'Y-m-d H:i:s' ώρα Ελλάδας
    $ordD  = substr($ordDt, 0, 10);
    $dtMs  = xxf_dt($ordDt);
    $dMs   = xxf_dt($ordD);
    $yr    = (int)substr($ordD, 0, 4);
    $mo    = (int)substr($ordD, 5, 2);
    $pay   = ($cust['payment'] ?? null) === null ? null : (int)$cust['payment'];

    foreach ($groups as $gi => [$gname, $tabs]) {
        foreach ($tabs as $ti => [$tn, $blob]) {
            [$fs, $p2] = xxf_fields($blob);
            $R = xxf_rows($blob, $fs, $p2);
            $ft = array_column($fs, 'type', 'name');

            if ($tn === '#STDSALDOC.FINDOC') {
                $f = $R[0];
                xxf_set($f, $ft, 'TRDR', (int)$cust['id']);
                xxf_set($f, $ft, 'TRDR_CODE', (string)$cust['code']);
                foreach (['TRNDATE', 'BGDOCDATE', 'INSDATEN'] as $k) {
                    xxf_set($f, $ft, $k, $dMs);
                }
                foreach (['APPRVDATE', 'BGDOCDATE1', 'INSDATE', 'SOTIME', 'UPDDATE'] as $k) {
                    xxf_set($f, $ft, $k, $dtMs);
                }
                xxf_set($f, $ft, 'FISCPRD', $yr);
                xxf_set($f, $ft, 'PERIOD', $mo);
                xxf_set($f, $ft, 'COMMENTS', 'B2B ' . $o['order_no']);
                xxf_set($f, $ft, 'REMARKS', (string)$o['order_no']);
                xxf_set($f, $ft, 'PAYMENT', $pay);
                xxf_set($f, $ft, 'SHIPMENT', null);
                xxf_set($f, $ft, 'SERIESNUM', 0);
                xxf_set($f, $ft, 'TAXSERIESNUM', null);
                xxf_set($f, $ft, 'FINCODE', null);
                xxf_set($f, $ft, 'POSGUID', null);
                xxf_set($f, $ft, 'ISPRINT', 0);
                foreach (['TURNOVR', 'TTURNOVR', 'LTURNOVR', 'NETAMNT', 'TNETAMNT', 'LNETAMNT'] as $k) {
                    xxf_set($f, $ft, $k, $net);
                }
                foreach (['VATAMNT', 'TVATAMNT', 'LVATAMNT'] as $k) {
                    xxf_set($f, $ft, $k, $vat);
                }
                foreach (['SUMAMNT', 'SUMTAMNT', 'SUMLAMNT'] as $k) {
                    xxf_set($f, $ft, $k, $tot);
                }
                $R = [$f];
            } elseif ($tn === '#STDSALDOC.MTRDOC') {
                $r = $R[0];
                xxf_set($r, $ft, 'QTY', $qty);
                xxf_set($r, $ft, 'QTY1', $qty);
                foreach (['SHIPPINGADDR', 'SHPZIP', 'SHPCITY', 'SOCARRIER', 'TRUCKS', 'TRUCKSNO'] as $k) {
                    xxf_set($r, $ft, $k, null);
                }
                $R = [$r];
            } elseif ($tn === '#STDSALDOC.MTRLINES') {
                $t = $R[0];
                $R = [];
                foreach (array_values($lines) as $i => $l) {
                    $r = $t;
                    $n = round((float)$l['net'], 2);
                    $v = round((float)$l['vat'], 2);
                    xxf_set($r, $ft, 'MTRLINES', $i + 1);
                    xxf_set($r, $ft, 'LINENUM', $i + 1);
                    xxf_set($r, $ft, 'MTRL', (int)$l['item_id']);
                    xxf_set($r, $ft, 'MTRL_CODE', (string)$l['code']);
                    xxf_set($r, $ft, 'VAT', (int)$l['vat_code']);
                    xxf_set($r, $ft, 'MTRUNIT', (int)$l['mtrunit']);
                    xxf_set($r, $ft, 'QTY', (float)$l['qty']);
                    xxf_set($r, $ft, 'QTY1', (float)$l['qty']);
                    xxf_set($r, $ft, 'PRICE', (float)$l['price']);
                    xxf_set($r, $ft, 'PRICE1', (float)$l['price']);
                    foreach (['LINEVAL', 'LLINEVAL', 'NETLINEVAL', 'LNETLINEVAL', 'TRNLINEVAL', 'LTRNLINEVAL'] as $k) {
                        xxf_set($r, $ft, $k, $n);
                    }
                    xxf_set($r, $ft, 'VATAMNT', $v);
                    xxf_set($r, $ft, 'LVATAMNT', $v);
                    xxf_set($r, $ft, 'SXPERC', round($n + $v, 2));
                    $R[] = $r;
                }
            } elseif ($tn === '#STDSALDOC.VATANAL') {
                $t = $R[0];
                $R = [];
                $i = 1;
                foreach ($vanal as $vc => [$n, $v]) {
                    $r = $t;
                    xxf_set($r, $ft, 'LINENUM', $i++);
                    xxf_set($r, $ft, 'VAT', $vc);
                    xxf_set($r, $ft, 'SUBVAL', round($n, 2));
                    xxf_set($r, $ft, 'LSUBVAL', round($n, 2));
                    xxf_set($r, $ft, 'VATVAL', round($v, 2));
                    xxf_set($r, $ft, 'LVATVAL', round($v, 2));
                    $R[] = $r;
                }
            } elseif (in_array($tn, ['#STDSALDOC.FINPAYTERMS', '#STDSALDOC.SNLINES',
                                    '#STDSALDOC.FPAYTRMS2', '#STDSALDOC.EXPANAL',
                                    '#STDSALDOC.ABCTRNLINES'], true)) {
                $R = [];
            }
            $groups[$gi][1][$ti][1] = xxf_build($blob, $fs, $p2, $R);
        }
    }

    // assemble: header ως έχει + groups
    $data = substr($tpl, 0, 0x1c);
    foreach ($groups as [$gname, $tabs]) {
        $data .= chr(strlen($gname)) . $gname . pack('V', count($tabs));
        foreach ($tabs as [, $blob]) {
            $data .= pack('V', strlen($blob)) . $blob;
        }
    }
    return $data;
}
