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
      <a href="/cart">Καλάθι<?= empty($_SESSION['cart']) ? '' : ' (' . count($_SESSION['cart']) . ')' ?></a>
      <a href="/orders">Παραγγελίες</a>
      <a href="/ledger">Καρτέλα</a>
      <a href="/invoices">Τιμολόγια</a>
      <a href="/password">Κωδικός</a>
      <a href="/logout">Έξοδος</a>
    </nav>
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
