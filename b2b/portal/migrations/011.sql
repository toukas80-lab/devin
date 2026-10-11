-- B2B-16 (MySQL 8): αγαπημένα πελάτη (το sync δεν αγγίζει τον πίνακα).
CREATE TABLE IF NOT EXISTS favorites (
  customer_id INT      NOT NULL,
  item_id     INT      NOT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (customer_id, item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
