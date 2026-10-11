<?php
declare(strict_types=1);

function auth_locked(PDO $db, string $email): bool
{
    $st = $db->prepare(
        'SELECT COUNT(*) FROM login_attempts
         WHERE email=? AND success=0
           AND attempted_at > (NOW() - INTERVAL 15 MINUTE)'
    );
    $st->execute([$email]);
    return (int)$st->fetchColumn() >= 5;
}

function auth_locked_ip(PDO $db): bool
{
    $st = $db->prepare(
        'SELECT COUNT(*) FROM login_attempts
         WHERE ip=? AND success=0
           AND attempted_at > (NOW() - INTERVAL 15 MINUTE)'
    );
    $st->execute([$_SERVER['REMOTE_ADDR'] ?? '']);
    return (int)$st->fetchColumn() >= 20;
}

function auth_log(PDO $db, string $email, bool $ok): void
{
    $db->prepare(
        'INSERT INTO login_attempts (email, ip, success, attempted_at)
         VALUES (?,?,?,NOW())'
    )->execute([$email, $_SERVER['REMOTE_ADDR'] ?? '', $ok ? 1 : 0]);
}

function auth_clear(PDO $db, string $email): void
{
    $db->prepare('DELETE FROM login_attempts WHERE email=?')->execute([$email]);
}
