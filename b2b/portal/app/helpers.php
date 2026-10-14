<?php
declare(strict_types=1);

function e(mixed $v): string
{
    return htmlspecialchars((string)$v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function money(mixed $v): string
{
    return number_format((float)$v, 2, ',', '.');
}

const B2B_DISC = 40.0;

function price_info(float $pr): array
{
    $disc = 0.0;
    $eff  = 0.0;
    if ($pr > 0) {
        $disc = B2B_DISC;
        $eff  = round($pr * (1 - $disc / 100), 2);
    }
    return ['w' => $pr, 'disc' => $disc, 'eff' => $eff];
}

function qtyf(mixed $v): string
{
    $f = (float)$v;
    return $f == (int)$f ? (string)(int)$f : number_format($f, 2, ',', '.');
}

function is_post(): bool
{
    return ($_SERVER['REQUEST_METHOD'] ?? '') === 'POST';
}

function redirect(string $path): never
{
    header('Location: ' . $path, true, 303);
    exit;
}

function flash(string $msg, string $cls = 'ok'): void
{
    $_SESSION['flash'][] = [$msg, $cls];
}

function flashes(): array
{
    $f = $_SESSION['flash'] ?? [];
    unset($_SESSION['flash']);
    return $f;
}

function csrf_token(): string
{
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf" value="' . csrf_token() . '">';
}

function csrf_check(): void
{
    $t = $_POST['csrf'] ?? '';
    if (!is_string($t) || !hash_equals(csrf_token(), $t)) {
        http_response_code(419);
        exit('CSRF');
    }
}

function user(): ?array
{
    return $_SESSION['user'] ?? null;
}

function require_user(): array
{
    $u = user();
    if ($u === null) {
        redirect('/login');
    }
    if (!empty($u['must_change'])) {
        redirect('/password');
    }
    return $u;
}

function send_mail(string $to, string $subject, string $body): void
{
    $c = cfg();
    $h = "MIME-Version: 1.0\r\n"
       . "Content-Type: text/plain; charset=UTF-8\r\n"
       . 'From: ' . $c['mail_from'] . "\r\n";
    @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, $h);
}

function send_mail_att(string $to, string $subject, string $body,
                       string $fname, string $data): void
{
    $c = cfg();
    $b = '=_' . bin2hex(random_bytes(12));
    $h = "MIME-Version: 1.0\r\n"
       . "Content-Type: multipart/mixed; boundary=\"$b\"\r\n"
       . 'From: ' . $c['mail_from'] . "\r\n";
    $m = "--$b\r\n"
       . "Content-Type: text/plain; charset=UTF-8\r\n"
       . "Content-Transfer-Encoding: base64\r\n\r\n"
       . chunk_split(base64_encode($body))
       . "--$b\r\n"
       . "Content-Type: application/octet-stream; name=\"$fname\"\r\n"
       . "Content-Transfer-Encoding: base64\r\n"
       . "Content-Disposition: attachment; filename=\"$fname\"\r\n\r\n"
       . chunk_split(base64_encode($data))
       . "--$b--\r\n";
    @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $m, $h);
}

function dmy($d): string
{
    $d = (string)$d;
    if ($d === '') {
        return '';
    }
    if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $d)) {
        return substr($d, 8, 2) . '/' . substr($d, 5, 2) . '/' . substr($d, 0, 4);
    }
    if (preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/', $d)) {
        return substr($d, 8, 2) . '/' . substr($d, 5, 2) . '/'
             . substr($d, 0, 4) . ' ' . substr($d, 11, 5);
    }
    return $d;
}
