<?php
// B2B-46 test: φτιάχνει test_out.XXF με τα στοιχεία του template
// (W-000007, 14/10/2026 12:52:28, πελ. 3837/TRDR 158486, 03137 x1 + 02576 x2).
// Τρέξε: php test_xxf.php  →  μετά: python cmp_ref.py test_out.XXF
// Επιτρεπτές διαφορές από το template: ΜΟΝΟ SOTIME/UPDDATE/APPRVDATE/INSDATE/BGDOCDATE1.
declare(strict_types=1);

require __DIR__ . '/../portal/app/xxf.php';

$data = order_xxf(
    ['order_no' => 'W-000007', 'created_at' => '2026-10-14 12:52:28'],
    ['id' => 158486, 'code' => '3837', 'payment' => null],
    [
        ['item_id' => 121126, 'code' => '03137', 'qty' => 1.0, 'price' => 5.0,
         'net' => 5.0, 'vat' => 1.2, 'vat_code' => 1410, 'mtrunit' => 101],
        ['item_id' => 118519, 'code' => '02576', 'qty' => 2.0, 'price' => 10.0,
         'net' => 20.0, 'vat' => 4.8, 'vat_code' => 1410, 'mtrunit' => 101],
    ]
);
file_put_contents(__DIR__ . '/test_out.XXF', $data);
echo 'test_out.XXF ' . strlen($data) . " bytes\n";
