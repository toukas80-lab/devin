<?php
declare(strict_types=1);

$base   = dirname(__DIR__, 2) . '/b2b_private';
$config = require $base . '/config.php';
define('PUBLIC_DIR', __DIR__);
require $base . '/app/bootstrap.php';
boot($config);

$r = $_GET['r'] ?? '';
if (!is_string($r)) {
    $r = '';
}
$r = trim($r, '/');

if ($r === 'api/sync') {
    api_sync();
} elseif ($r === 'api/image') {
    api_image();
} elseif (str_starts_with($r, 'admin')) {
    admin_dispatch($r);
} else {
    match ($r) {
        ''         => page_home(),
        'login'    => page_login(),
        'password' => page_password(),
        'logout'   => page_logout(),
        'catalog'  => page_catalog(),
        'quick'    => page_quick(),
        'fav'      => page_fav(),
        'favorites' => page_favorites(),
        'cart'     => page_cart(),
        'order'    => page_order(),
        'orders'   => page_orders(),
        'reorder'  => page_reorder(),
        'ledger'   => page_ledger(),
        'invoices' => page_invoices(),
        default    => page_not_found(),
    };
}
