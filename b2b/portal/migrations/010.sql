-- B2B-15 (MySQL 8): κατασκευαστής είδους στον κατάλογο.
-- Τρέξε μέσα στην υπάρχουσα βάση b2b ΠΡΙΝ το επόμενο upload των datasets.

ALTER TABLE items
  ADD COLUMN manufacturer VARCHAR(100) NOT NULL DEFAULT '' AFTER stock,
  ADD KEY idx_items_manf (manufacturer);
