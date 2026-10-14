<?php
declare(strict_types=1);

function boot(array $config): void
{
    $GLOBALS['B2B_CONFIG'] = $config;
    mb_internal_encoding('UTF-8');
    date_default_timezone_set('Europe/Athens');

    $secure = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
    session_set_cookie_params([
        'lifetime' => 0,
        'path'     => '/',
        'secure'   => $secure,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    session_start();

    require_once __DIR__ . '/db.php';
    require_once __DIR__ . '/helpers.php';
    require_once __DIR__ . '/xxf.php';
    require_once __DIR__ . '/auth.php';
    require_once __DIR__ . '/layout.php';
    require_once __DIR__ . '/pages.php';
    require_once __DIR__ . '/admin.php';
    require_once __DIR__ . '/api.php';
}
