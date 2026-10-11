-- B2B portal schema (MySQL 8.0, utf8mb4) — run inside the existing b2b database.
CREATE TABLE IF NOT EXISTS item_groups (
  id    INT          NOT NULL PRIMARY KEY,
  name  VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS items (
  id       INT           NOT NULL PRIMARY KEY,
  code     VARCHAR(50)   NOT NULL,
  name     VARCHAR(255)  NOT NULL,
  group_id INT           NULL,
  unit     VARCHAR(32)   NULL,
  vat_pct  DECIMAL(6,2)  NOT NULL DEFAULT 0,
  price_w  DECIMAL(12,4) NOT NULL DEFAULT 0,
  stock    DECIMAL(14,3) NOT NULL DEFAULT 0,
  manufacturer VARCHAR(100) NOT NULL DEFAULT '',
  KEY idx_items_group (group_id),
  KEY idx_items_code (code),
  KEY idx_items_manf (manufacturer)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS customers (
  id      INT           NOT NULL PRIMARY KEY,
  code    VARCHAR(25)   NOT NULL,
  name    VARCHAR(255)  NOT NULL,
  email   VARCHAR(191)  NOT NULL DEFAULT '',
  afm     VARCHAR(9)    NOT NULL DEFAULT '',
  balance DECIMAL(14,2) NOT NULL DEFAULT 0,
  KEY idx_customers_email (email),
  KEY idx_customers_afm (afm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prices (
  customer_id INT           NOT NULL,
  item_id     INT           NOT NULL,
  price       DECIMAL(12,4) NOT NULL,
  date        DATE          NOT NULL,
  PRIMARY KEY (customer_id, item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ledger (
  seq         BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
  customer_id INT          NOT NULL,
  date        DATE         NOT NULL,
  doc         VARCHAR(64)  NOT NULL DEFAULT '',
  descr       VARCHAR(255) NOT NULL DEFAULT '',
  debit       DECIMAL(14,2) NOT NULL DEFAULT 0,
  credit      DECIMAL(14,2) NOT NULL DEFAULT 0,
  opening     TINYINT(1)   NOT NULL DEFAULT 0,
  KEY idx_ledger_cust (customer_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS invoices (
  findoc_id   INT           NOT NULL PRIMARY KEY,
  customer_id INT           NOT NULL,
  date        DATE          NOT NULL,
  doc         VARCHAR(64)   NOT NULL DEFAULT '',
  net         DECIMAL(14,2) NOT NULL DEFAULT 0,
  vat         DECIMAL(14,2) NOT NULL DEFAULT 0,
  total       DECIMAL(14,2) NOT NULL DEFAULT 0,
  KEY idx_invoices_cust (customer_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS users (
  id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
  customer_id INT          NOT NULL,
  email       VARCHAR(191) NULL,
  pass_hash   VARCHAR(255) NOT NULL,
  must_change TINYINT(1)   NOT NULL DEFAULT 1,
  is_active   TINYINT(1)   NOT NULL DEFAULT 1,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login  DATETIME     NULL,
  UNIQUE KEY uq_users_cust (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS orders (
  id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
  order_no    VARCHAR(12)  NOT NULL,
  customer_id INT          NOT NULL,
  user_id     INT          NOT NULL,
  status      ENUM('new','seen','done','cancelled') NOT NULL DEFAULT 'new',
  net         DECIMAL(14,2) NOT NULL DEFAULT 0,
  vat         DECIMAL(14,2) NOT NULL DEFAULT 0,
  total       DECIMAL(14,2) NOT NULL DEFAULT 0,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_orders_no (order_no),
  KEY idx_orders_cust (customer_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_lines (
  id       INT           NOT NULL AUTO_INCREMENT PRIMARY KEY,
  order_id INT           NOT NULL,
  item_id  INT           NOT NULL,
  code     VARCHAR(50)   NOT NULL,
  name     VARCHAR(255)  NOT NULL,
  qty      DECIMAL(12,3) NOT NULL,
  price    DECIMAL(12,4) NOT NULL,
  net      DECIMAL(14,2) NOT NULL,
  vat_pct  DECIMAL(6,2)  NOT NULL DEFAULT 0,
  vat      DECIMAL(14,2) NOT NULL,
  total    DECIMAL(14,2) NOT NULL,
  KEY idx_olines_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sync_log (
  id        INT         NOT NULL AUTO_INCREMENT PRIMARY KEY,
  dataset   VARCHAR(32) NOT NULL,
  row_count INT         NOT NULL,
  synced_at DATETIME    NOT NULL,
  ip        VARCHAR(45) NOT NULL DEFAULT '',
  KEY idx_sync_ds (dataset, synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS login_attempts (
  id           INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
  email        VARCHAR(191) NOT NULL,
  ip           VARCHAR(45)  NOT NULL DEFAULT '',
  success      TINYINT(1)   NOT NULL DEFAULT 0,
  attempted_at DATETIME     NOT NULL,
  KEY idx_attempts (email, attempted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
