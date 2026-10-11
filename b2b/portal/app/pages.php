<?php
declare(strict_types=1);

function page_not_found(): void
{
    http_response_code(404);
    page_top('Δεν βρέθηκε');
    echo '<h1>404</h1><p>Η σελίδα δεν βρέθηκε.</p>';
    page_bottom();
}

function page_login(): void
{
    if (user()) {
        redirect('/');
    }
    $err = '';
    if (is_post()) {
        csrf_check();
        $afm = preg_replace('/[\s\x{00A0}.\-]+/u', '', mb_strtoupper((string)($_POST['afm'] ?? '')));
        $afm = preg_replace('/^(E|Ε)(L|Λ)/u', '', (string)$afm);
        if (preg_match('/^\d{8}$/', (string)$afm)) {
            $afm = '0' . $afm;
        }
        $pass = (string)($_POST['pass'] ?? '');
        $db = db();
        if (auth_locked($db, $afm) || auth_locked_ip($db)) {
            $err = 'Ο λογαριασμός κλειδώθηκε για 15 λεπτά λόγω επαναλαμμένων αποτυχιών.';
        } else {
            $st = $db->prepare(
                'SELECT id, code, name, email FROM customers WHERE afm = ? LIMIT 1'
            );
            $st->execute([$afm]);
            $cust = $st->fetch();
            $u = false;
            if ($cust) {
                $st = $db->prepare(
                    'SELECT id, pass_hash, is_active, must_change
                     FROM users WHERE customer_id = ? LIMIT 1'
                );
                $st->execute([$cust['id']]);
                $u = $st->fetch();
                if (!$u && $pass === $afm) {
                    try {
                        $db->prepare(
                            'INSERT INTO users (customer_id, email, pass_hash, must_change)
                             VALUES (?,?,?,1)'
                        )->execute([
                            $cust['id'],
                            $cust['email'] !== '' ? $cust['email'] : null,
                            password_hash($afm, PASSWORD_DEFAULT),
                        ]);
                    } catch (Throwable $ex) {
                        // παράλληλη δημιουργία — ξαναδιαβάζουμε τη γραμμή
                    }
                    $st->execute([$cust['id']]);
                    $u = $st->fetch();
                }
            }
            if ($u && (int)$u['is_active'] === 1
                && password_verify($pass, $u['pass_hash'])) {
                auth_log($db, $afm, true);
                auth_clear($db, $afm);
                session_regenerate_id(true);
                $_SESSION['user'] = [
                    'id'          => (int)$u['id'],
                    'customer_id' => (int)$cust['id'],
                    'email'       => (string)($cust['email'] ?? ''),
                    'name'        => $cust['name'],
                    'code'        => $cust['code'],
                    'must_change' => (int)$u['must_change'],
                ];
                $db->prepare('UPDATE users SET last_login = NOW() WHERE id = ?')
                   ->execute([$u['id']]);
                redirect((int)$u['must_change'] === 1 ? '/password' : '/');
            }
            auth_log($db, $afm, false);
            $err = 'Λάθος ΑΦΜ ή κωδικός.';
        }
    }
    page_top('Σύνδεση');
    ?>
<div class="card login">
  <h1>Σύνδεση πελάτη</h1>
  <?php if ($err !== ''): ?><div class="flash err"><?= e($err) ?></div><?php endif; ?>
  <form method="post" action="/login">
    <?= csrf_field() ?>
    <label>ΑΦΜ
      <input type="text" name="afm" required autofocus autocomplete="username" maxlength="13">
    </label>
    <label>Κωδικός
      <input type="password" name="pass" required autocomplete="current-password">
    </label>
    <button type="submit">Είσοδος</button>
  </form>
</div>
<?php
    page_bottom();
}

function page_password(): void
{
    $u = user();
    if ($u === null) {
        redirect('/login');
    }
    $db = db();
    $err = '';
    if (is_post()) {
        csrf_check();
        $p1 = (string)($_POST['pass1'] ?? '');
        $p2 = (string)($_POST['pass2'] ?? '');
        $st = $db->prepare('SELECT afm FROM customers WHERE id = ?');
        $st->execute([$u['customer_id']]);
        $afm = (string)$st->fetchColumn();
        if (mb_strlen($p1) < 8) {
            $err = 'Ο κωδικός πρέπει να έχει τουλάχιστον 8 χαρακτήρες.';
        } elseif ($p1 !== $p2) {
            $err = 'Οι κωδικοί δεν ταιριάζουν.';
        } elseif ($p1 === $afm) {
            $err = 'Ο νέος κωδικός δεν μπορεί να είναι το ΑΦΜ.';
        } else {
            $db->prepare('UPDATE users SET pass_hash = ?, must_change = 0 WHERE id = ?')
               ->execute([password_hash($p1, PASSWORD_DEFAULT), $u['id']]);
            session_regenerate_id(true);
            $_SESSION['user']['must_change'] = 0;
            flash('Ο κωδικός άλλαξε επιτυχώς.');
            redirect('/');
        }
    }
    page_top('Αλλαγή κωδικού');
    ?>
<div class="card login">
  <h1>Αλλαγή κωδικού</h1>
  <?php if (!empty($u['must_change'])): ?>
    <p>Για λόγους ασφαλείας ορίστε προσωπικό κωδικό (όχι το ΑΦΜ).</p>
  <?php endif; ?>
  <?php if ($err !== ''): ?><div class="flash err"><?= e($err) ?></div><?php endif; ?>
  <form method="post" action="/password">
    <?= csrf_field() ?>
    <label>Νέος κωδικός
      <input type="password" name="pass1" required minlength="8" autocomplete="new-password">
    </label>
    <label>Επανάληψη κωδικού
      <input type="password" name="pass2" required minlength="8" autocomplete="new-password">
    </label>
    <button type="submit">Αποθήκευση</button>
  </form>
</div>
<?php
    page_bottom();
}

function page_logout(): void
{
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', time() - 3600, $p['path'], $p['domain'], $p['secure'], $p['httponly']);
    }
    session_destroy();
    redirect('/login');
}

function cust_price(PDO $db, int $cid, int $itemId): float
{
    $st = $db->prepare(
        'SELECT i.price_w, p.price AS special
         FROM items i LEFT JOIN prices p
           ON p.item_id = i.id AND p.customer_id = ?
         WHERE i.id = ? LIMIT 1'
    );
    $st->execute([$cid, $itemId]);
    $r = $st->fetch();
    if (!$r) {
        return 0.0;
    }
    return $r['special'] !== null ? (float)$r['special'] : (float)$r['price_w'];
}

function page_home(): void
{
    $u = require_user();
    $db = db();
    $st = $db->prepare('SELECT balance FROM customers WHERE id = ?');
    $st->execute([$u['customer_id']]);
    $bal = (float)$st->fetchColumn();

    $st = $db->prepare(
        'SELECT order_no, status, total, created_at
         FROM orders WHERE customer_id = ?
         ORDER BY created_at DESC LIMIT 5'
    );
    $st->execute([$u['customer_id']]);
    $orders = $st->fetchAll();

    page_top('Αρχική');
    ?>
<h1>Καλωσήρθατε, <?= e($u['name']) ?></h1>
<div class="grid2">
  <div class="card">
    <h2>Υπόλοιπο</h2>
    <p class="big"><?= money($bal) ?> &euro;</p>
    <p><a href="/ledger">Δείτε την καρτέλα &rarr;</a></p>
  </div>
  <div class="card">
    <h2>Τελευταίες παραγγελίες</h2>
    <?php if (!$orders): ?>
      <p>Δεν υπάρχουν παραγγελίες.</p>
    <?php else: ?>
    <table>
      <tr><th>Αριθμός</th><th>Ημ/νία</th><th>Σύνολο</th><th>Κατάσταση</th></tr>
      <?php foreach ($orders as $o): ?>
      <tr>
        <td><?= e($o['order_no']) ?></td>
        <td><?= e(dmy($o['created_at'])) ?></td>
        <td class="r"><?= money($o['total']) ?> &euro;</td>
        <td><?= e(status_label($o['status'])) ?></td>
      </tr>
      <?php endforeach; ?>
    </table>
    <?php endif; ?>
  </div>
</div>
<?php
    page_bottom();
}

function status_label(string $s): string
{
    return match ($s) {
        'new'       => 'Νέα',
        'seen'      => 'Σε εξέλιξη',
        'done'      => 'Ολοκληρώθηκε',
        'cancelled' => 'Ακυρώθηκε',
        default     => $s,
    };
}

function page_catalog(): void
{
    $u   = require_user();
    $db  = db();
    $cid = $u['customer_id'];
    $q   = trim((string)($_GET['q'] ?? ''));
    $g   = (int)($_GET['g'] ?? 0);
    $pg  = max(1, (int)($_GET['p'] ?? 1));
    $per = 24;

    if (is_post()) {
        csrf_check();
        $iid = (int)($_POST['item_id'] ?? 0);
        $qty = (float)str_replace(',', '.', (string)($_POST['qty'] ?? '0'));
        if ($iid > 0 && $qty > 0) {
            $price = cust_price($db, $cid, $iid);
            if ($price <= 0) {
                flash('Το είδος δεν έχει τιμή — ρωτήστε τιμή.', 'err');
            } else {
                $_SESSION['cart'][$iid] = ($_SESSION['cart'][$iid] ?? 0) + $qty;
                flash('Προστέθηκε στο καλάθι.');
            }
        }
        redirect('/catalog?' . http_build_query(['q' => $q, 'g' => $g, 'p' => $pg]));
    }

    $where = '1=1';
    $par   = [];
    if ($q !== '') {
        $where .= ' AND (i.code LIKE ? OR i.name LIKE ?)';
        $par[] = '%' . $q . '%';
        $par[] = '%' . $q . '%';
    }
    if ($g > 0) {
        $where .= ' AND i.group_id = ?';
        $par[] = $g;
    }
    $st = $db->prepare("SELECT COUNT(*) FROM items i WHERE $where");
    $st->execute($par);
    $total = (int)$st->fetchColumn();
    $pages = max(1, (int)ceil($total / $per));
    $pg    = min($pg, $pages);
    $off   = ($pg - 1) * $per;

    $st = $db->prepare(
        "SELECT i.id, i.code, i.name, i.unit, i.price_w, i.vat_pct, i.img_ver,
                g.name AS gname, p.price AS special,
                (f.item_id IS NOT NULL) AS fav
         FROM items i
         LEFT JOIN item_groups g ON g.id = i.group_id
         LEFT JOIN prices p ON p.item_id = i.id AND p.customer_id = ?
         LEFT JOIN favorites f ON f.item_id = i.id AND f.customer_id = ?
         WHERE $where
         ORDER BY i.code
         LIMIT $per OFFSET $off"
    );
    $st->execute(array_merge([$cid, $cid], $par));
    $items = $st->fetchAll();

    $groups = $db->query('SELECT id, name FROM item_groups ORDER BY name')->fetchAll();

    page_top('Κατάλογος');
    ?>
<h1>Κατάλογος</h1>
<form class="filters" method="get" action="/catalog">
  <input type="search" name="q" value="<?= e($q) ?>" placeholder="Αναζήτηση κωδικού ή περιγραφής">
  <select name="g" onchange="this.form.submit()">
    <option value="0">Όλες οι ομάδες</option>
    <?php foreach ($groups as $gr): ?>
    <option value="<?= (int)$gr['id'] ?>" <?= $g === (int)$gr['id'] ? 'selected' : '' ?>><?= e($gr['name']) ?></option>
    <?php endforeach; ?>
  </select>
  <button type="submit">Αναζήτηση</button>
</form>
<div class="scroll">
<table>
  <tr><th></th><th>Κωδικός</th><th>Είδος</th><th>ΜΜ</th><th class="r">Τιμή</th><th></th><th></th></tr>
  <?php foreach ($items as $it):
      $eff = $it['special'] !== null ? (float)$it['special'] : (float)$it['price_w'];
      $v   = (string)$it['img_ver']; ?>
  <tr>
    <td>
      <?php if ($v !== ''): ?>
      <a href="/img/<?= e(rawurlencode($it['code'])) ?>.jpg?v=<?= e($v) ?>" target="_blank"><img class="thumb" src="/img/<?= e(rawurlencode($it['code'])) ?>.jpg?v=<?= e($v) ?>" loading="lazy" width="64" height="64" alt=""></a>
      <?php endif; ?>
    </td>
    <td><?= e($it['code']) ?></td>
    <td><?= e($it['name']) ?></td>
    <td><?= e($it['unit'] ?? '') ?></td>
    <td class="r">
      <?php if ($eff > 0): ?>
        <?= money($eff) ?> &euro;
      <?php else: ?>
        <span class="muted">Ρωτήστε τιμή</span>
      <?php endif; ?>
    </td>
    <td class="r">
      <?php if ($eff > 0): ?>
      <form method="post" action="/catalog" class="inline">
        <?= csrf_field() ?>
        <input type="hidden" name="item_id" value="<?= (int)$it['id'] ?>">
        <input class="qty" type="number" name="qty" value="1" min="0.001" step="any">
        <button type="submit">+</button>
      </form>
      <?php endif; ?>
    </td>
    <td class="r">
      <form method="post" action="/fav" class="inline"><?= csrf_field() ?><input type="hidden" name="item_id" value="<?= (int)$it['id'] ?>"><input type="hidden" name="back" value="<?= e('/catalog?' . http_build_query(['q' => $q, 'g' => $g, 'p' => $pg])) ?>"><button type="submit" class="fav" title="Αγαπημένο"><?= $it['fav'] ? '★' : '☆' ?></button></form>
    </td>
  </tr>
  <?php endforeach; ?>
</table>
</div>
<?php if ($pages > 1): ?>
<nav class="pages">
  <?php for ($i = 1; $i <= $pages; $i++): ?>
    <?php if ($i === $pg): ?>
      <strong><?= $i ?></strong>
    <?php else: ?>
      <a href="/catalog?<?= e(http_build_query(['q' => $q, 'g' => $g, 'p' => $i])) ?>"><?= $i ?></a>
    <?php endif; ?>
  <?php endfor; ?>
</nav>
<?php endif; ?>
<p class="muted">Οι τιμές είναι χωρίς ΦΠΑ.</p>
<?php
    page_bottom();
}

function page_cart(): void
{
    $u   = require_user();
    $db  = db();
    $cid = $u['customer_id'];
    $cart = $_SESSION['cart'] ?? [];

    if (is_post()) {
        csrf_check();
        if (isset($_POST['clear'])) {
            $_SESSION['cart'] = [];
            redirect('/cart');
        }
        foreach ((array)($_POST['qty'] ?? []) as $iid => $qv) {
            $iid = (int)$iid;
            $qv  = (float)str_replace(',', '.', (string)$qv);
            if ($qv <= 0) {
                unset($_SESSION['cart'][$iid]);
            } else {
                $_SESSION['cart'][$iid] = $qv;
            }
        }
        redirect('/cart');
    }

    $lines = [];
    if ($cart) {
        $in  = implode(',', array_fill(0, count($cart), '?'));
        $st  = $db->prepare(
            "SELECT i.id, i.code, i.name, i.unit, i.vat_pct, i.stock, i.price_w,
                    p.price AS special
             FROM items i
             LEFT JOIN prices p ON p.item_id = i.id AND p.customer_id = ?
             WHERE i.id IN ($in)"
        );
        $st->execute(array_merge([$cid], array_map('intval', array_keys($cart))));
        foreach ($st->fetchAll() as $it) {
            $eff = $it['special'] !== null ? (float)$it['special'] : (float)$it['price_w'];
            $qty = (float)$cart[$it['id']];
            $net = round($eff * $qty, 2);
            $vat = round($net * (float)$it['vat_pct'] / 100, 2);
            $lines[] = [
                'it' => $it, 'qty' => $qty, 'price' => $eff,
                'net' => $net, 'vat' => $vat, 'total' => $net + $vat,
            ];
        }
    }

    page_top('Καλάθι');
    ?>
<h1>Καλάθι</h1>
<?php if (!$lines): ?>
  <p>Το καλάθι είναι άδειο. <a href="/catalog">Μετάβαση στον κατάλογο &rarr;</a></p>
<?php else: ?>
<form method="post" action="/cart">
  <?= csrf_field() ?>
<div class="scroll">
<table>
  <tr><th>Κωδικός</th><th>Είδος</th><th class="r">Τιμή</th><th class="r">Ποσότητα</th><th class="r">Σύνολο</th></tr>
  <?php $tn = 0.0; $tv = 0.0; foreach ($lines as $l): $tn += $l['net']; $tv += $l['vat']; ?>
  <tr>
    <td><?= e($l['it']['code']) ?></td>
    <td>
      <?= e($l['it']['name']) ?>
      <?php if ($l['qty'] > (float)$l['it']['stock']): ?>
        <div class="warn">Χαμηλό απόθεμα – μπορεί να υπάρξει καθυστέρηση</div>
      <?php endif; ?>
    </td>
    <td class="r"><?= money($l['price']) ?> &euro;</td>
    <td class="r">
      <input class="qty" type="number" name="qty[<?= (int)$l['it']['id'] ?>]"
             value="<?= e((string)(float)$l['qty']) ?>" min="0" step="any">
    </td>
    <td class="r"><?= money($l['total']) ?> &euro;</td>
  </tr>
  <?php endforeach; ?>
</table>
</div>
<p class="totals">
  Καθαρή αξία: <strong><?= money($tn) ?> &euro;</strong><br>
  ΦΠΑ: <strong><?= money($tv) ?> &euro;</strong><br>
  Γενικό σύνολο: <strong><?= money($tn + $tv) ?> &euro;</strong>
</p>
<p>
  <button type="submit">Ενημέρωση ποσοτήτων</button>
  <button type="submit" name="clear" value="1" formnovalidate>Άδειασμα</button>
</p>
</form>
<form method="post" action="/order">
  <?= csrf_field() ?>
  <button type="submit" class="primary">Αποστολή παραγγελίας</button>
</form>
<?php endif; ?>
<?php
    page_bottom();
}

function page_order(): void
{
    $u   = require_user();
    $db  = db();
    $cid = $u['customer_id'];

    if (is_post()) {
        csrf_check();
        $cart = $_SESSION['cart'] ?? [];
        if (!$cart) {
            flash('Το καλάθι είναι άδειο.', 'err');
            redirect('/cart');
        }
        $in = implode(',', array_fill(0, count($cart), '?'));
        $st = $db->prepare(
            "SELECT i.id, i.code, i.name, i.vat_pct, i.price_w, p.price AS special
             FROM items i
             LEFT JOIN prices p ON p.item_id = i.id AND p.customer_id = ?
             WHERE i.id IN ($in)"
        );
        $st->execute(array_merge([$cid], array_map('intval', array_keys($cart))));
        $rows = $st->fetchAll();

        $lines = [];
        $tn = $tv = 0.0;
        foreach ($rows as $it) {
            $eff = $it['special'] !== null ? (float)$it['special'] : (float)$it['price_w'];
            if ($eff <= 0) {
                flash('Το είδος ' . $it['code'] . ' δεν έχει τιμή και αφαιρέθηκε.', 'err');
                unset($_SESSION['cart'][$it['id']]);
                redirect('/cart');
            }
            $qty = (float)$cart[$it['id']];
            $net = round($eff * $qty, 2);
            $vat = round($net * (float)$it['vat_pct'] / 100, 2);
            $tn += $net;
            $tv += $vat;
            $lines[] = [$it, $qty, $eff, $net, $vat, $net + $vat];
        }

        $orderNo = null;
        for ($try = 0; $try < 3 && $orderNo === null; $try++) {
            try {
                $db->beginTransaction();
                $next = (int)$db->query(
                    "SELECT COALESCE(MAX(CAST(SUBSTRING(order_no,3) AS UNSIGNED)),0)+1 FROM orders"
                )->fetchColumn();
                $orderNo = sprintf('W-%06d', $next);
                $db->prepare(
                    'INSERT INTO orders (order_no, customer_id, user_id, net, vat, total)
                     VALUES (?,?,?,?,?,?)'
                )->execute([$orderNo, $cid, $u['id'], $tn, $tv, $tn + $tv]);
                $oid = (int)$db->lastInsertId();
                $ins = $db->prepare(
                    'INSERT INTO order_lines
                       (order_id, item_id, code, name, qty, price, net, vat_pct, vat, total)
                     VALUES (?,?,?,?,?,?,?,?,?,?)'
                );
                foreach ($lines as [$it, $qty, $eff, $net, $vat, $tot]) {
                    $ins->execute([$oid, $it['id'], $it['code'], $it['name'],
                                   $qty, $eff, $net, $it['vat_pct'], $vat, $tot]);
                }
                $db->commit();
            } catch (Throwable $ex) {
                if ($db->inTransaction()) {
                    $db->rollBack();
                }
                $orderNo = null;
                if ($try === 2) {
                    throw $ex;
                }
            }
        }
        $_SESSION['cart'] = [];

        $c = cfg();
        $body = "Νέα παραγγελία $orderNo\n"
              . 'Πελάτης: ' . $u['code'] . ' ' . $u['name'] . "\n\n";
        foreach ($lines as [$it, $qty, $eff, $net, $vat, $tot]) {
            $body .= $it['code'] . ' x' . qtyf($qty) . ' @ ' . money($eff) . " = " . money($tot) . "\n";
        }
        $body .= "\nΣύνολο: " . money($tn + $tv) . " ευρώ (με ΦΠΑ)\n";
        send_mail($c['notify_email'], "Παραγγελία $orderNo", $body);
        if ($u['email'] !== '') {
            send_mail($u['email'], "Επιβεβαίωση παραγγελίας $orderNo",
                      "Η παραγγελία σας $orderNo καταχωρήθηκε.\n" . $body);
        }
        flash("Η παραγγελία $orderNo καταχωρήθηκε.");
        redirect('/orders');
    }

    $id = (int)($_GET['id'] ?? 0);
    $st = $db->prepare('SELECT * FROM orders WHERE id = ? AND customer_id = ?');
    $st->execute([$id, $cid]);
    $o = $st->fetch();
    if (!$o) {
        page_not_found();
        return;
    }
    $st = $db->prepare('SELECT * FROM order_lines WHERE order_id = ? ORDER BY id');
    $st->execute([$id]);
    $lines = $st->fetchAll();

    page_top('Παραγγελία ' . $o['order_no']);
    ?>
<h1>Παραγγελία <?= e($o['order_no']) ?></h1>
<p><?= e(dmy($o['created_at'])) ?> · Κατάσταση: <strong><?= e(status_label($o['status'])) ?></strong></p>
<div class="scroll">
<table>
  <tr><th>Κωδικός</th><th>Είδος</th><th class="r">Ποσ.</th><th class="r">Τιμή</th><th class="r">Σύνολο</th></tr>
  <?php foreach ($lines as $l): ?>
  <tr>
    <td><?= e($l['code']) ?></td>
    <td><?= e($l['name']) ?></td>
    <td class="r"><?= e(qtyf($l['qty'])) ?></td>
    <td class="r"><?= money($l['price']) ?> &euro;</td>
    <td class="r"><?= money($l['total']) ?> &euro;</td>
  </tr>
  <?php endforeach; ?>
</table>
</div>
<p class="totals">
  Καθαρή: <?= money($o['net']) ?> &euro; · ΦΠΑ: <?= money($o['vat']) ?> &euro; ·
  Σύνολο: <strong><?= money($o['total']) ?> &euro;</strong>
</p>
<form method="post" action="/reorder" class="inline"><?= csrf_field() ?><input type="hidden" name="order_id" value="<?= (int)$o['id'] ?>"><button type="submit">Ξανά στο καλάθι</button></form>
<?php
    page_bottom();
}

function page_orders(): void
{
    $u  = require_user();
    $st = db()->prepare(
        'SELECT id, order_no, status, total, created_at
         FROM orders WHERE customer_id = ? ORDER BY created_at DESC'
    );
    $st->execute([$u['customer_id']]);
    $orders = $st->fetchAll();

    page_top('Οι παραγγελίες μου');
    ?>
<h1>Οι παραγγελίες μου</h1>
<?php if (!$orders): ?>
  <p>Δεν υπάρχουν παραγγελίες.</p>
<?php else: ?>
<div class="scroll">
<table>
  <tr><th>Αριθμός</th><th>Ημ/νία</th><th class="r">Σύνολο</th><th>Κατάσταση</th><th></th></tr>
  <?php foreach ($orders as $o): ?>
  <tr>
    <td><?= e($o['order_no']) ?></td>
    <td><?= e(dmy($o['created_at'])) ?></td>
    <td class="r"><?= money($o['total']) ?> &euro;</td>
    <td><?= e(status_label($o['status'])) ?></td>
    <td><a href="/order?id=<?= (int)$o['id'] ?>">Προβολή</a>
        <form method="post" action="/reorder" class="inline"><?= csrf_field() ?><input type="hidden" name="order_id" value="<?= (int)$o['id'] ?>"><button type="submit">Ξανά στο καλάθι</button></form></td>
  </tr>
  <?php endforeach; ?>
</table>
</div>
<?php endif; ?>
<?php
    page_bottom();
}

function page_reorder(): void
{
    $u   = require_user();
    $db  = db();
    $cid = $u['customer_id'];
    if (!is_post()) {
        redirect('/orders');
    }
    csrf_check();
    $oid = (int)($_POST['order_id'] ?? 0);
    $st  = $db->prepare('SELECT id FROM orders WHERE id = ? AND customer_id = ?');
    $st->execute([$oid, $cid]);
    if (!$st->fetch()) {
        page_not_found();
        return;
    }
    $st = $db->prepare(
        'SELECT l.item_id, l.code, l.qty, i.id AS live
         FROM order_lines l
         LEFT JOIN items i ON i.id = l.item_id
         WHERE l.order_id = ? ORDER BY l.id'
    );
    $st->execute([$oid]);
    $n    = 0;
    $gone = [];
    foreach ($st->fetchAll() as $l) {
        if ($l['live'] !== null && cust_price($db, $cid, (int)$l['item_id']) > 0) {
            $iid = (int)$l['item_id'];
            $_SESSION['cart'][$iid] = ($_SESSION['cart'][$iid] ?? 0) + (float)$l['qty'];
            $n++;
        } else {
            $gone[] = $l['code'];
        }
    }
    flash("Μπήκαν $n είδη στο καλάθι.");
    if ($gone) {
        flash('Δεν είναι πλέον διαθέσιμα: ' . implode(', ', $gone), 'err');
    }
    redirect('/cart');
}

function page_quick(): void
{
    $u      = require_user();
    $db     = db();
    $cid    = $u['customer_id'];
    $errors = [];
    $keep   = '';

    if (is_post()) {
        csrf_check();
        $raw   = (string)($_POST['lines'] ?? '');
        $todo  = [];
        foreach (preg_split('/\r\n|\n|\r/', $raw) as $i => $line) {
            $line = trim($line);
            if ($line !== '') {
                $todo[] = [$i + 1, $line];
            }
        }
        if (count($todo) > 200) {
            flash('Έως 200 γραμμές.', 'err');
            $keep = $raw;
        } else {
            $n    = 0;
            $find = $db->prepare('SELECT id FROM items WHERE code = ?');
            foreach ($todo as [$ln, $line]) {
                $parts = preg_match('/[\t; ]/', $line)
                    ? preg_split('/[\t; ]+/', $line, 2)
                    : explode(',', $line, 2);
                $code = trim($parts[0] ?? '');
                $qtyr = str_replace(',', '.', trim($parts[1] ?? ''));
                $err  = null;
                $iid  = 0;
                if ($code === '' || !is_numeric($qtyr) || (float)$qtyr <= 0) {
                    $err = 'άκυρη ποσότητα';
                } else {
                    $find->execute([$code]);
                    $iid = (int)$find->fetchColumn();
                    if ($iid <= 0) {
                        $err = 'δεν βρέθηκε';
                    } elseif (cust_price($db, $cid, $iid) <= 0) {
                        $err = 'ρωτήστε τιμή';
                    }
                }
                if ($err !== null) {
                    $errors[] = "Γραμμή $ln: $line — $err";
                    $keep    .= ($keep === '' ? '' : "\n") . $line;
                } else {
                    $_SESSION['cart'][$iid] =
                        ($_SESSION['cart'][$iid] ?? 0) + (float)$qtyr;
                    $n++;
                }
            }
            if (!$errors) {
                flash("Μπήκαν $n είδη στο καλάθι.");
                redirect('/cart');
            }
            flash("Μπήκαν $n είδη στο καλάθι.");
        }
    }

    page_top('Γρήγορη παραγγελία');
    ?>
<h1>Γρήγορη παραγγελία</h1>
<p>Μία γραμμή ανά είδος: κωδικός και ποσότητα. Μπορείτε να επικολλήσετε δύο στήλες από Excel.</p>
<?php if ($errors): ?>
<ul class="err">
  <?php foreach ($errors as $err): ?><li><?= e($err) ?></li><?php endforeach; ?>
</ul>
<?php endif; ?>
<form method="post" action="/quick"><?= csrf_field() ?><textarea name="lines" rows="15" cols="40"><?= e($keep) ?></textarea><br><button type="submit">Προσθήκη στο καλάθι</button></form>
<?php
    page_bottom();
}

function page_fav(): void
{
    $u = require_user();
    if (!is_post()) {
        redirect('/catalog');
    }
    csrf_check();
    $db  = db();
    $cid = $u['customer_id'];
    $iid = (int)($_POST['item_id'] ?? 0);
    if ($iid > 0) {
        $st = $db->prepare(
            'SELECT 1 FROM favorites WHERE customer_id = ? AND item_id = ?'
        );
        $st->execute([$cid, $iid]);
        if ($st->fetch()) {
            $db->prepare(
                'DELETE FROM favorites WHERE customer_id = ? AND item_id = ?'
            )->execute([$cid, $iid]);
        } else {
            $st = $db->prepare('SELECT 1 FROM items WHERE id = ?');
            $st->execute([$iid]);
            if ($st->fetch()) {
                $db->prepare(
                    'INSERT IGNORE INTO favorites (customer_id, item_id) VALUES (?,?)'
                )->execute([$cid, $iid]);
            }
        }
    }
    $back = (string)($_POST['back'] ?? '');
    if (!str_starts_with($back, '/catalog') && !str_starts_with($back, '/favorites')) {
        $back = '/catalog';
    }
    redirect($back);
}

function page_favorites(): void
{
    $u   = require_user();
    $db  = db();
    $cid = $u['customer_id'];

    if (is_post()) {
        csrf_check();
        $n = 0;
        foreach ((array)($_POST['qty'] ?? []) as $iid => $qv) {
            $iid = (int)$iid;
            $qv  = (float)str_replace(',', '.', (string)$qv);
            if ($iid > 0 && $qv > 0 && cust_price($db, $cid, $iid) > 0) {
                $_SESSION['cart'][$iid] = ($_SESSION['cart'][$iid] ?? 0) + $qv;
                $n++;
            }
        }
        flash("Μπήκαν $n είδη στο καλάθι.");
        redirect('/cart');
    }

    $st = $db->prepare(
        'SELECT i.id, i.code, i.name, i.unit, i.price_w, p.price AS special
         FROM favorites f
         JOIN items i ON i.id = f.item_id
         LEFT JOIN prices p ON p.item_id = i.id AND p.customer_id = ?
         WHERE f.customer_id = ?
         ORDER BY i.code'
    );
    $st->execute([$cid, $cid]);
    $rows = $st->fetchAll();

    page_top('Αγαπημένα');
    ?>
<h1>Αγαπημένα</h1>
<?php if (!$rows): ?>
<p>Δεν έχετε αγαπημένα. Πατήστε ☆ στον κατάλογο.</p>
<?php else: ?>
<form method="post" action="/favorites">
  <?= csrf_field() ?>
  <input type="hidden" name="back" value="/favorites">
<div class="scroll">
<table>
  <tr><th>Κωδικός</th><th>Είδος</th><th>ΜΜ</th><th class="r">Τιμή</th><th class="r">Ποσότητα</th><th></th></tr>
  <?php foreach ($rows as $r): $eff = $r['special'] !== null ? (float)$r['special'] : (float)$r['price_w']; ?>
  <tr>
    <td><?= e($r['code']) ?></td>
    <td><?= e($r['name']) ?></td>
    <td><?= e($r['unit'] ?? '') ?></td>
    <td class="r">
      <?php if ($eff > 0): ?>
        <?= money($eff) ?> &euro;
      <?php else: ?>
        <span class="muted">Ρωτήστε τιμή</span>
      <?php endif; ?>
    </td>
    <td class="r">
      <?php if ($eff > 0): ?>
      <input class="qty" type="number" name="qty[<?= (int)$r['id'] ?>]" value="" min="0" step="any">
      <?php endif; ?>
    </td>
    <td class="r">
      <button type="submit" formaction="/fav" name="item_id" value="<?= (int)$r['id'] ?>" class="fav" title="Αφαίρεση">★</button>
    </td>
  </tr>
  <?php endforeach; ?>
</table>
</div>
<p><button type="submit">Προσθήκη στο καλάθι</button></p>
</form>
<?php endif; ?>
<?php
    page_bottom();
}

function date_param(string $k): string
{
    $v = (string)($_GET[$k] ?? '');
    if ($v === '') {
        return '';
    }
    $d = DateTime::createFromFormat('Y-m-d', $v);
    return ($d !== false && $d->format('Y-m-d') === $v) ? $v : '';
}

function page_ledger(): void
{
    $u  = require_user();
    $st = db()->prepare('SELECT * FROM ledger WHERE customer_id = ? ORDER BY seq');
    $st->execute([$u['customer_id']]);
    $rows = $st->fetchAll();

    $from = date_param('from');
    $to   = date_param('to');
    if ($from !== '' && $to !== '' && $from > $to) {
        [$from, $to] = [$to, $from];
    }

    $open  = 0.0;
    $shown = [];
    foreach ($rows as $r) {
        if ($from !== '' && $r['date'] < $from) {
            $open += (float)$r['debit'] - (float)$r['credit'];
            continue;
        }
        if ($to !== '' && $r['date'] > $to) {
            continue;
        }
        $shown[] = $r;
    }

    page_top('Καρτέλα');
    ?>
<h1>Καρτέλα</h1>
<form method="get" action="/ledger" class="filters">
  Από <input type="date" name="from" value="<?= e($from) ?>">
  Έως <input type="date" name="to" value="<?= e($to) ?>">
  <button type="submit">Εφαρμογή</button>
  <a href="/ledger">Καθαρισμός</a>
</form>
<p class="muted">Εμφανίζονται οι κινήσεις των τελευταίων 3 ετών.</p>
<?php if (!$shown): ?>
  <p>Δεν υπάρχουν κινήσεις στο διάστημα αυτό.</p>
<?php else: ?>
<div class="scroll">
<table>
  <tr><th>Ημ/νία</th><th>Παραστατικό</th><th>Περιγραφή</th><th class="r">Χρέωση</th><th class="r">Πίστωση</th><th class="r">Υπόλοιπο</th></tr>
  <?php $bal = $open; ?>
  <?php if ($from !== ''): ?>
  <tr>
    <td><?= e(dmy($from)) ?></td>
    <td></td>
    <td>Υπόλοιπο μεταφοράς</td>
    <td class="r"><?= $open > 0 ? money($open) : '' ?></td>
    <td class="r"><?= $open < 0 ? money(-$open) : '' ?></td>
    <td class="r"><?= money($open) ?></td>
  </tr>
  <?php endif; ?>
  <?php $sd = $sc = 0.0; foreach ($shown as $r): $bal += (float)$r['debit'] - (float)$r['credit']; $sd += (float)$r['debit']; $sc += (float)$r['credit']; ?>
  <tr>
    <td><?= e(dmy($r['date'])) ?></td>
    <td><?= e($r['doc']) ?></td>
    <td><?= e($r['descr']) ?></td>
    <td class="r"><?= (float)$r['debit']  > 0 ? money($r['debit'])  : '' ?></td>
    <td class="r"><?= (float)$r['credit'] > 0 ? money($r['credit']) : '' ?></td>
    <td class="r"><?= money($bal) ?></td>
  </tr>
  <?php endforeach; ?>
  <tr>
    <td colspan="3"><strong>Σύνολα</strong></td>
    <td class="r"><strong><?= money($sd) ?></strong></td>
    <td class="r"><strong><?= money($sc) ?></strong></td>
    <td class="r"><strong><?= money($bal) ?></strong></td>
  </tr>
</table>
</div>
<?php endif; ?>
<?php
    page_bottom();
}

function page_invoices(): void
{
    $u    = require_user();
    $from = date_param('from');
    $to   = date_param('to');
    if ($from !== '' && $to !== '' && $from > $to) {
        [$from, $to] = [$to, $from];
    }
    $sql = 'SELECT date, doc, net, vat, total
            FROM invoices WHERE customer_id = ?';
    $par = [$u['customer_id']];
    if ($from !== '') {
        $sql .= ' AND date >= ?';
        $par[] = $from;
    }
    if ($to !== '') {
        $sql .= ' AND date <= ?';
        $par[] = $to;
    }
    $sql .= ' ORDER BY date DESC, findoc_id DESC';
    $st = db()->prepare($sql);
    $st->execute($par);
    $rows = $st->fetchAll();

    page_top('Τιμολόγια');
    ?>
<h1>Τιμολόγια</h1>
<form method="get" action="/invoices" class="filters">
  Από <input type="date" name="from" value="<?= e($from) ?>">
  Έως <input type="date" name="to" value="<?= e($to) ?>">
  <button type="submit">Εφαρμογή</button>
  <a href="/invoices">Καθαρισμός</a>
</form>
<p class="muted">Εμφανίζονται τα παραστατικά των τελευταίων 3 ετών.</p>
<?php if (!$rows): ?>
  <p>Δεν υπάρχουν παραστατικά στο διάστημα αυτό.</p>
<?php else: ?>
<div class="scroll">
<table>
  <tr><th>Ημ/νία</th><th>Παραστατικό</th><th class="r">Καθαρή</th><th class="r">ΦΠΑ</th><th class="r">Σύνολο</th></tr>
  <?php $sn = $sv = $su = 0.0; foreach ($rows as $r):
      $sn += (float)$r['net']; $sv += (float)$r['vat']; $su += (float)$r['total']; ?>
  <tr>
    <td><?= e(dmy($r['date'])) ?></td>
    <td><?= e($r['doc']) ?></td>
    <td class="r"><?= money($r['net']) ?> &euro;</td>
    <td class="r"><?= money($r['vat']) ?> &euro;</td>
    <td class="r"><?= money($r['total']) ?> &euro;</td>
  </tr>
  <?php endforeach; ?>
  <tr>
    <td colspan="2"><strong>Σύνολο</strong></td>
    <td class="r"><strong><?= money($sn) ?> &euro;</strong></td>
    <td class="r"><strong><?= money($sv) ?> &euro;</strong></td>
    <td class="r"><strong><?= money($su) ?> &euro;</strong></td>
  </tr>
</table>
</div>
<?php endif; ?>
<?php
    page_bottom();
}
