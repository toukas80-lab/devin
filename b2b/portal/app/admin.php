<?php
declare(strict_types=1);

function is_admin(): bool
{
    return !empty($_SESSION['admin']);
}

function require_admin(): void
{
    if (!is_admin()) {
        redirect('/admin/login');
    }
}

function admin_dispatch(string $r): void
{
    if ($r === 'admin/login') {
        admin_login();
        return;
    }
    if ($r === 'admin/logout') {
        unset($_SESSION['admin']);
        redirect('/admin/login');
    }
    require_admin();
    match ($r) {
        'admin', 'admin/'        => admin_home(),
        'admin/status'           => admin_status(),
        'admin/users'            => admin_users(),
        'admin/order.csv'        => admin_order_csv(),
        default                  => page_not_found(),
    };
}

function admin_login(): void
{
    if (is_admin()) {
        redirect('/admin');
    }
    $err = '';
    if (is_post()) {
        csrf_check();
        $key = 'admin#login';
        $db  = db();
        if (auth_locked($db, $key)) {
            $err = 'Πολλές αποτυχημένες προσπάθειες — δοκιμάστε σε 15 λεπτά.';
        } elseif (password_verify((string)($_POST['pass'] ?? ''),
                                  (string)cfg()['admin_pass_hash'])) {
            auth_clear($db, $key);
            session_regenerate_id(true);
            $_SESSION['admin'] = true;
            redirect('/admin');
        } else {
            auth_log($db, $key, false);
            $err = 'Λάθος κωδικός.';
        }
    }
    page_top('Admin');
    ?>
<div class="card login">
  <h1>Διαχείριση</h1>
  <?php if ($err !== ''): ?><div class="flash err"><?= e($err) ?></div><?php endif; ?>
  <form method="post" action="/admin/login">
    <?= csrf_field() ?>
    <label>Κωδικός
      <input type="password" name="pass" required autofocus>
    </label>
    <button type="submit">Είσοδος</button>
  </form>
</div>
<?php
    page_bottom();
}

function admin_home(): void
{
    $db = db();
    $orders = $db->query(
        'SELECT o.id, o.order_no, o.status, o.total, o.created_at,
                c.code, c.name
         FROM orders o JOIN customers c ON c.id = o.customer_id
         ORDER BY o.created_at DESC LIMIT 100'
    )->fetchAll();
    $sync = $db->query(
        'SELECT s.dataset, s.row_count, s.synced_at
         FROM sync_log s
         JOIN (SELECT dataset, MAX(synced_at) m FROM sync_log GROUP BY dataset) x
           ON x.dataset = s.dataset AND x.m = s.synced_at
         ORDER BY s.dataset'
    )->fetchAll();

    page_top('Admin');
    ?>
<h1>Διαχείριση <a class="btn" href="/admin/users">Χρήστες</a> <a class="btn" href="/admin/logout">Έξοδος</a></h1>
<div class="card">
  <h2>Τελευταίος συγχρονισμός</h2>
  <?php if (!$sync): ?><p>Δεν έχει γίνει συγχρονισμός.</p><?php else: ?>
  <table>
    <tr><th>Dataset</th><th class="r">Εγγραφές</th><th>Ημ/νία</th></tr>
    <?php foreach ($sync as $s): ?>
    <tr><td><?= e($s['dataset']) ?></td><td class="r"><?= (int)$s['row_count'] ?></td><td><?= e(dmy($s['synced_at'])) ?></td></tr>
    <?php endforeach; ?>
  </table>
  <?php endif; ?>
</div>
<div class="card">
  <h2>Παραγγελίες</h2>
  <?php if (!$orders): ?><p>Καμία παραγγελία.</p><?php else: ?>
  <div class="scroll">
  <table>
    <tr><th>Αριθμός</th><th>Ημ/νία</th><th>Πελάτης</th><th class="r">Σύνολο</th><th>Κατάσταση</th><th></th></tr>
    <?php foreach ($orders as $o): ?>
    <tr>
      <td><?= e($o['order_no']) ?></td>
      <td><?= e(dmy($o['created_at'])) ?></td>
      <td><?= e($o['code']) ?> <?= e($o['name']) ?></td>
      <td class="r"><?= money($o['total']) ?> &euro;</td>
      <td>
        <form method="post" action="/admin/status" class="inline">
          <?= csrf_field() ?>
          <input type="hidden" name="order_id" value="<?= (int)$o['id'] ?>">
          <select name="status" onchange="this.form.submit()">
            <?php foreach (['new', 'seen', 'done', 'cancelled'] as $s): ?>
            <option value="<?= $s ?>" <?= $o['status'] === $s ? 'selected' : '' ?>><?= e(status_label($s)) ?></option>
            <?php endforeach; ?>
          </select>
        </form>
      </td>
      <td><a href="/admin/order.csv?id=<?= (int)$o['id'] ?>">CSV</a></td>
    </tr>
    <?php endforeach; ?>
  </table>
  </div>
  <?php endif; ?>
</div>
<?php
    page_bottom();
}

function admin_status(): void
{
    require_admin();
    if (!is_post()) {
        redirect('/admin');
    }
    csrf_check();
    $oid    = (int)($_POST['order_id'] ?? 0);
    $status = (string)($_POST['status'] ?? '');
    if ($oid > 0 && in_array($status, ['new', 'seen', 'done', 'cancelled'], true)) {
        $st = db()->prepare(
            'SELECT o.order_no, o.status, o.total, o.created_at, c.email
             FROM orders o LEFT JOIN customers c ON c.id = o.customer_id
             WHERE o.id = ?'
        );
        $st->execute([$oid]);
        $o = $st->fetch();
        if (!$o) {
            flash('Η παραγγελία δεν βρέθηκε.', 'err');
            redirect('/admin');
        }
        db()->prepare('UPDATE orders SET status = ? WHERE id = ?')
           ->execute([$status, $oid]);
        $sent = false;
        if (in_array($status, ['seen', 'done', 'cancelled'], true)
            && $status !== $o['status']
            && trim((string)$o['email']) !== ''
            && filter_var($o['email'], FILTER_VALIDATE_EMAIL)) {
            send_mail(
                $o['email'],
                'Παραγγελία ' . $o['order_no'] . ': ' . status_label($status),
                "Η κατάσταση της παραγγελίας σας άλλαξε.\n\n"
                . 'Παραγγελία: ' . $o['order_no'] . "\n"
                . 'Ημερομηνία: ' . dmy($o['created_at']) . "\n"
                . 'Σύνολο: ' . money($o['total']) . " ευρώ (με ΦΠΑ)\n"
                . 'Νέα κατάσταση: ' . status_label($status) . "\n"
            );
            $sent = true;
        }
        flash('Η κατάσταση ενημερώθηκε.'
              . ($sent ? ' Στάλθηκε email στον πελάτη.' : ''));
    }
    redirect('/admin');
}

function admin_order_csv(): void
{
    require_admin();
    $id = (int)($_GET['id'] ?? 0);
    $db = db();
    $st = $db->prepare('SELECT order_no FROM orders WHERE id = ?');
    $st->execute([$id]);
    $no = $st->fetchColumn();
    if ($no === false) {
        page_not_found();
        return;
    }
    $st = $db->prepare('SELECT code, qty, price, price_w, disc_pct FROM order_lines WHERE order_id = ? ORDER BY id');
    $st->execute([$id]);

    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $no . '.csv"');
    $out = fopen('php://output', 'w');
    fputcsv($out, ['code', 'qty', 'price', 'price_w', 'disc_pct']);
    while ($r = $st->fetch()) {
        fputcsv($out, [$r['code'], $r['qty'], $r['price'], $r['price_w'], $r['disc_pct']]);
    }
    fclose($out);
    exit;
}

function admin_users(): void
{
    require_admin();
    $db = db();

    if (is_post()) {
        csrf_check();
        if (isset($_POST['toggle'])) {
            $uid = (int)$_POST['toggle'];
            $db->prepare('UPDATE users SET is_active = 1 - is_active WHERE id = ?')->execute([$uid]);
            flash('Η κατάσταση χρήστη άλλαξε.');
        } elseif (isset($_POST['reset'])) {
            $uid = (int)$_POST['reset'];
            $st = $db->prepare(
                'SELECT c.afm FROM users u JOIN customers c ON c.id = u.customer_id
                 WHERE u.id = ?'
            );
            $st->execute([$uid]);
            $afm = (string)$st->fetchColumn();
            if ($afm !== '') {
                $db->prepare('UPDATE users SET pass_hash = ?, must_change = 1 WHERE id = ?')
                   ->execute([password_hash($afm, PASSWORD_DEFAULT), $uid]);
                flash('Ο κωδικός επαναφέρθηκε στο ΑΦΜ — θα ζητηθεί αλλαγή στην είσοδο.');
            }
        }
        redirect('/admin/users');
    }

    $users = $db->query(
        'SELECT u.id, u.is_active, u.must_change, u.last_login, c.code, c.name
         FROM users u JOIN customers c ON c.id = u.customer_id
         ORDER BY c.code'
    )->fetchAll();

    page_top('Χρήστες');
    ?>
<h1>Χρήστες <a class="btn" href="/admin">&larr; Πίσω</a></h1>
<div class="card">
  <h2>Λογαριασμοί</h2>
  <?php if (!$users): ?><p>Κανένας λογαριασμός.</p><?php else: ?>
  <div class="scroll">
  <table>
    <tr><th>Κωδικός</th><th>Πελάτης</th><th>Τελ. είσοδος</th><th>Κατάσταση</th><th>must_change</th><th></th></tr>
    <?php foreach ($users as $x): ?>
    <tr>
      <td><?= e($x['code']) ?></td>
      <td><?= e($x['name']) ?></td>
      <td><?= e(dmy($x['last_login'] ?? '—')) ?></td>
      <td><?= (int)$x['is_active'] === 1 ? 'Ενεργός' : 'Ανενεργός' ?></td>
      <td><?= (int)$x['must_change'] === 1 ? 'Ναι' : '—' ?></td>
      <td>
        <form method="post" action="/admin/users" class="inline">
          <?= csrf_field() ?>
          <button type="submit" name="toggle" value="<?= (int)$x['id'] ?>">
            <?= (int)$x['is_active'] === 1 ? 'Απενεργοποίηση' : 'Ενεργοποίηση' ?>
          </button>
          <button type="submit" name="reset" value="<?= (int)$x['id'] ?>">Επαναφορά κωδικού</button>
        </form>
      </td>
    </tr>
    <?php endforeach; ?>
  </table>
  </div>
  <?php endif; ?>
</div>
<?php
    page_bottom();
}
