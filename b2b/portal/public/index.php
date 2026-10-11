<?php
declare(strict_types=1);

$base   = dirname(__DIR__, 2) . '/b2b_private';
$config = require $base . '/config.php';
require $base . '/app/bootstrap.php';
boot($config);

$r = $_GET['r'] ?? '';
if (!is_string($r)) {
    $r = '';
}
$r = trim($r, '/');

if ($r === 'api/sync') {
    api_sync();
} elseif (str_starts_with($r, 'admin')) {
    admin_dispatch($r);
} else {
    match ($r) {
        ''         => page_home(),
        'login'    => page_login(),
        'password' => page_password(),
        'logout'   => page_logout(),
        'catalog'  => page_catalog(),
        'cart'     => page_cart(),
        'order'    => page_order(),
        'orders'   => page_orders(),
        'ledger'   => page_ledger(),
        'invoices' => page_invoices(),
        default    => page_not_found(),
    };
}
