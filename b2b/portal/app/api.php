<?php
declare(strict_types=1);

function api_auth(): bool
{
    $token = $_SERVER['HTTP_X_SYNC_TOKEN'] ?? '';
    if (!is_string($token)
        || !hash_equals((string)cfg()['sync_token_sha256'], hash('sha256', $token))) {
        http_response_code(401);
        echo '{"ok":false,"error":"unauthorized"}';
        return false;
    }
    return true;
}

function api_order_status(): void
{
    $raw = file_get_contents('php://input');
    if (($_SERVER['HTTP_CONTENT_ENCODING'] ?? '') === 'gzip') {
        $raw = gzdecode($raw);
    }
    $data = json_decode((string)$raw, true);
    if (!is_array($data)) {
        http_response_code(400);
        echo '{"error":"bad json"}';
        return;
    }
    $db = db();
    try {
        $seen = $db->prepare(
            "UPDATE orders SET status='seen'
             WHERE order_no = ? AND status = 'new'"
        );
        $done = $db->prepare(
            "UPDATE orders SET status='done'
             WHERE order_no = ? AND status IN ('new','seen')"
        );
        $sel = $db->prepare(
            'SELECT o.order_no, o.total, o.created_at, c.email
             FROM orders o LEFT JOIN customers c ON c.id = o.customer_id
             WHERE o.order_no = ?'
        );
        $changed = 0;
        foreach ($data as $r) {
            if (!is_array($r)) {
                continue;
            }
            $orderNo = trim((string)($r['order_no'] ?? ''));
            if ($orderNo === '') {
                continue;
            }
            $target = !empty($r['done']) ? 'done' : 'seen';
            $st = $target === 'done' ? $done : $seen;
            $st->execute([$orderNo]);
            if ($st->rowCount() === 1) {
                $changed++;
                $sel->execute([$orderNo]);
                $o = $sel->fetch();
                if ($o) {
                    status_mail($o, $target);
                }
            }
        }
        $db->prepare(
            'INSERT INTO sync_log (dataset, row_count, synced_at, ip)
             VALUES (?,?,NOW(),?)'
        )->execute(['order_status', $changed, $_SERVER['REMOTE_ADDR'] ?? '']);
    } catch (Throwable $ex) {
        http_response_code(500);
        echo '{"error":"db"}';
        return;
    }
    echo json_encode(['ok' => true, 'rows' => count($data), 'changed' => $changed]);
}

function api_image(): void
{
    header('Content-Type: application/json; charset=utf-8');

    if (!is_post()) {
        http_response_code(405);
        echo '{"ok":false,"error":"POST only"}';
        return;
    }
    if (!api_auth()) {
        return;
    }
    $code = (string)($_GET['code'] ?? '');
    if (!preg_match('/^[A-Za-z0-9_-]{1,50}$/', $code)) {
        http_response_code(400);
        echo '{"ok":false,"error":"bad code"}';
        return;
    }
    $raw = file_get_contents('php://input');
    if ($raw === false) {
        $raw = '';
    }
    if (strlen($raw) === 0 || strlen($raw) > 2 * 1024 * 1024) {
        http_response_code(413);
        echo '{"ok":false,"error":"too large"}';
        return;
    }
    $info = @getimagesizefromstring($raw);
    if ($info === false || $info[2] !== IMAGETYPE_JPEG) {
        http_response_code(415);
        echo '{"ok":false,"error":"jpeg only"}';
        return;
    }
    $dir = PUBLIC_DIR . '/img';
    if (!is_dir($dir) && !mkdir($dir, 0755, true)) {
        http_response_code(500);
        echo '{"ok":false,"error":"mkdir"}';
        return;
    }
    $tmp = tempnam($dir, '.tmp');
    if ($tmp === false || file_put_contents($tmp, $raw) === false) {
        if ($tmp !== false) {
            @unlink($tmp);
        }
        http_response_code(500);
        echo '{"ok":false,"error":"write"}';
        return;
    }
    if (!rename($tmp, $dir . '/' . $code . '.jpg')) {
        @unlink($tmp);
        http_response_code(500);
        echo '{"ok":false,"error":"rename"}';
        return;
    }
    @chmod($dir . '/' . $code . '.jpg', 0644);
    echo json_encode(['ok' => true, 'code' => $code, 'bytes' => strlen($raw)]);
}

function api_sync(): void
{
    header('Content-Type: application/json; charset=utf-8');

    if (!is_post()) {
        http_response_code(405);
        echo '{"ok":false,"error":"POST only"}';
        return;
    }
    if (!api_auth()) {
        return;
    }
    $ds = (string)($_GET['dataset'] ?? '');
    if ($ds === 'order_status') {
        api_order_status();
        return;
    }
    $map = [
        'item_groups' => ['item_groups', ['id', 'name']],
        'items'       => ['items', ['id', 'code', 'name', 'group_id', 'chapter', 'unit', 'vat_pct', 'vat_code', 'mtrunit', 'price_w', 'price_r', 'stock', 'manufacturer', 'img_ver']],
        'customers'   => ['customers', ['id', 'code', 'name', 'email', 'afm', 'balance', 'payment', 'disc']],
        'prices'      => ['prices', ['customer_id', 'item_id', 'price', 'date']],
        'ledger'      => ['ledger', ['customer_id', 'date', 'doc', 'descr', 'debit', 'credit', 'opening']],
        'invoices'    => ['invoices', ['findoc_id', 'customer_id', 'date', 'doc', 'net', 'vat', 'total', 'einv_url']],
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
                if ($v === null && $cname === 'chapter') {
                    $v = '';
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
