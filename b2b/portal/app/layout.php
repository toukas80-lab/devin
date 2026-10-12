<?php
declare(strict_types=1);

function page_top(string $title): void
{
    $u = user();
    header('Content-Type: text/html; charset=utf-8');
    ?>
<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= e($title) ?> · B2B Φουντούκας</title>
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap bar">
    <a class="brand" href="/">B2B Φουντούκας</a>
    <?php if ($u): ?>
    <nav>
      <a href="/catalog">Κατάλογος</a>
      <a href="/pricelist">Τιμοκατάλογος PDF</a>
      <a href="/quick">Γρήγορη παραγγελία</a>
      <a href="/favorites">Αγαπημένα</a>
      <a href="/orders">Παραγγελίες</a>
      <a href="/ledger">Καρτέλα</a>
      <a href="/invoices">Τιμολόγια</a>
      <a href="/password">Κωδικός</a>
      <a href="/logout">Έξοδος</a>
    </nav>
    <?php $cn = count($_SESSION['cart'] ?? []); ?>
    <a class="cartbtn" href="/cart" title="Καλάθι">
      <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M7 18a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm10 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM5.2 4l.4 2H21l-2.2 8.6a2 2 0 0 1-1.9 1.4H8.1a2 2 0 0 1-2-1.6L3.4 2H1V0h4l.2 1"/></svg>
      Καλάθι<?php if ($cn > 0): ?> <span class="badge"><?= $cn ?></span><?php endif; ?>
    </a>
    <?php endif; ?>
  </div>
</header>
<main class="wrap">
<?php foreach (flashes() as $f): ?>
  <div class="flash <?= e($f[1]) ?>"><?= e($f[0]) ?></div>
<?php endforeach; ?>
<?php
}

function page_bottom(): void
{
    ?>
</main>
<footer class="wrap foot">B2B Πύλη Πελατών</footer>
</body>
</html>
<?php
}
