<?php
declare(strict_types=1);

function api_sync(): void
{
    header('Content-Type: application/json; charset=utf-8');

    if (!is_post()) {
        http_response_code(405);
        echo '{"ok":false,"error":"POST only"}';
        return;
    }
    $token = $_SERVER['HTTP_X_SYNC_TOKEN'] ?? '';
    if (!is_string($token)
        || !hash_equals((string)cfg()['sync_token_sha256'], hash('sha256', $token))) {
        http_response_code(401);
        echo '{"ok":false,"error":"unauthorized"}';
        return;
    }
    $ds = (string)($_GET['dataset'] ?? '');
    $map = [
        'item_groups' => ['item_groups', ['id', 'name']],
        'items'       => ['items', ['id', 'code', 'name', 'group_id', 'unit', 'vat_pct', 'price_w', 'stock']],
        'customers'   => ['customers', ['id', 'code', 'name', 'email', 'balance']],
        'prices'      => ['prices', ['customer_id', 'item_id', 'price', 'date']],
        'ledger'      => ['ledger', ['customer_id', 'date', 'doc', 'descr', 'debit', 'credit', 'opening']],
        'invoices'    => ['invoices', ['findoc_id', 'customer_id', 'date', 'doc', 'net', 'vat', 'total']],
    ];
    if (!isset($map[$ds])) {
        http_response_code(400);
        echo '{"ok":false,"error":"unknown dataset"}';
        return;
    }
    [$table, $cols] = $map[$ds];

    $raw = file_get_contents('php://input');
    if ($raw === false) {
        $raw = '';
    }
    $enc = $_SERVER['HTTP_CONTENT_ENCODING'] ?? '';
    if (stripos($enc, 'gzip') !== false) {
        $raw = gzdecode($raw);
    }
    if ($raw === false || $raw === '') {
        http_response_code(400);
        echo '{"ok":false,"error":"empty body"}';
        return;
    }
    $data = json_decode($raw, true);
    if (!is_array($data)) {
        http_response_code(400);
        echo '{"ok":false,"error":"bad json"}';
        return;
    }

    $db = db();
    $ph = '(' . implode(',', array_fill(0, count($cols), '?')) . ')';
    $cl = '`' . implode('`,`', $cols) . '`';
    try {
        $db->beginTransaction();
        $db->exec('DELETE FROM `' . $table . '`');
        $st = $db->prepare("INSERT INTO `$table` ($cl) VALUES $ph");
        $n = 0;
        foreach ($data as $row) {
            if (!is_array($row)) {
                continue;
            }
            $vals = [];
            foreach ($cols as $cname) {
                $v = $row[$cname] ?? null;
                if ($v === null && $cname === 'opening') {
                    $v = 0;
                }
                $vals[] = $v;
            }
            $st->execute($vals);
            $n++;
        }
        $db->prepare(
            'INSERT INTO sync_log (dataset, row_count, synced_at, ip) VALUES (?,?,NOW(),?)'
        )->execute([$ds, $n, $_SERVER['REMOTE_ADDR'] ?? '']);
        $db->commit();
        echo json_encode(['ok' => true, 'rows' => $n]);
    } catch (Throwable $ex) {
        if ($db->inTransaction()) {
            $db->rollBack();
        }
        http_response_code(500);
        echo '{"ok":false,"error":"db error"}';
    }
}
