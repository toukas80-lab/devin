<?php
// Αντιγραφή σε /b2b_private/config.php και συμπλήρωση πραγματικών τιμών.
// Το config.php ΔΕΝ μπαίνει στο repo.
return [
    'db_host'         => '127.0.0.1',
    'db_name'         => 'b2b',
    'db_user'         => 'b2b_user',
    'db_pass'         => 'CHANGE_ME',
    'sync_token'      => 'CHANGE_ME_LONG_RANDOM_TOKEN',
    'admin_pass_hash' => 'PASTE_password_hash_OUTPUT', // password_hash('...', PASSWORD_DEFAULT)
    'notify_email'    => 'orders@b2bfountoukas.gr',
    'mail_from'       => 'noreply@b2bfountoukas.gr',
];
