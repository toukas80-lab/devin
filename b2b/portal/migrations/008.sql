-- B2B-08 (MySQL 8): σύνδεση πελατών με ΑΦΜ + υποχρεωτική αλλαγή κωδικού.
-- Τρέξε μέσα στην υπάρχουσα βάση b2b ΠΡΙΝ το επόμενο upload των datasets.

ALTER TABLE customers
  ADD COLUMN afm VARCHAR(9) NOT NULL DEFAULT '' AFTER email,
  ADD KEY idx_customers_afm (afm);

ALTER TABLE users
  MODIFY COLUMN email VARCHAR(191) NULL,
  DROP INDEX uq_users_email,
  ADD COLUMN must_change TINYINT(1) NOT NULL DEFAULT 1 AFTER pass_hash;
