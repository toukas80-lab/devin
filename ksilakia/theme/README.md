# ksilakia.gr WordPress theme

Custom theme του e-shop https://ksilakia.gr (WooCommerce, Papaki hosting).

- Ζωντανό path στον server: `www/wp-content/themes/ksilakia/`
- Deploy ΜΟΝΟ από τον Devin στο cloud μέσω FTP (plain FTP, user `b2b@ksilakiagr`, host `ksilak.ftp.tb-hosting.com`). Το CLI του γραφείου δεν έχει FTP.
- Workflow: το CLI κάνει αλλαγές σε αυτόν τον φάκελο σε branch `ksilakia-*` → Devin κάνει review και ανεβάζει τα αλλαγμένα αρχεία μέσω FTP → verify live.
- Η σελίδα χονδρικής έχει slug `xondriki-b2b` (ΠΟΤΕ `b2b` — το πιάνει ο φάκελος της πύλης b2bfountoukas.gr στο ίδιο hosting).
- Στοιχεία B2B: ρόλος `wholesale_customer` (plugin woocommerce-wholesale-prices), αιτήσεις `ksilakia_b2b_status=pending`, έγκριση από wp-admin → Χρήστες. Email admin σε κάθε εγγραφή + αίτηση B2B.
- ΑΦΜ lookup: VIES (χωρίς κωδικούς) ή ΑΑΔΕ αν οριστούν `KSILAKIA_AADE_USER/PASS` στο wp-config.
- ΜΗΝ commit secrets: το SMTP password μένει στο wp-config/mu-plugin του server, όχι εδώ.
