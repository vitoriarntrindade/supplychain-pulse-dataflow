-- ============================================
-- Dimensões (catálogos)
-- ============================================
CREATE TABLE IF NOT EXISTS suppliers (
  id   BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS skus (
  id       BIGSERIAL PRIMARY KEY,
  sku_code TEXT NOT NULL UNIQUE
);

-- ============================================
-- FATO AGREGADO: Pedidos criados por dia e fornecedor
-- (saída do gold_orders_created)
-- ============================================
CREATE TABLE IF NOT EXISTS orders_created_daily (
  id            BIGSERIAL PRIMARY KEY,
  day           DATE      NOT NULL,                    -- vindo de .dt.date() no Polars
  supplier_id   BIGINT    NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
  total_orders  INTEGER   NOT NULL,
  total_qty     INTEGER   NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (day, supplier_id)
);
CREATE INDEX IF NOT EXISTS idx_ocd_day        ON orders_created_daily(day DESC);
CREATE INDEX IF NOT EXISTS idx_ocd_supplier   ON orders_created_daily(supplier_id);

-- ============================================
-- FATO AGREGADO: Atrasos por fornecedor (snapshot diário)
-- (saída do gold_orders_delayed)
-- ============================================
CREATE TABLE IF NOT EXISTS orders_delayed_daily (
  id              BIGSERIAL PRIMARY KEY,
  day             DATE      NOT NULL DEFAULT (CURRENT_DATE),  -- snapshot do dia do processamento
  supplier_id     BIGINT    NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
  delayed_orders  INTEGER   NOT NULL,
  avg_delay_days  NUMERIC(10,4) NOT NULL,                     -- média de dias de atraso
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (day, supplier_id)
);
CREATE INDEX IF NOT EXISTS idx_odd_day        ON orders_delayed_daily(day DESC);
CREATE INDEX IF NOT EXISTS idx_odd_supplier   ON orders_delayed_daily(supplier_id);

-- ============================================
-- FATO AGREGADO: Alertas de estoque por SKU (snapshot diário)
-- (saída do gold_inventory_alerts)
-- ============================================
CREATE TABLE IF NOT EXISTS inventory_alerts_daily (
  id               BIGSERIAL PRIMARY KEY,
  day              DATE      NOT NULL DEFAULT (CURRENT_DATE),
  sku_id           BIGINT    NOT NULL REFERENCES skus(id) ON DELETE RESTRICT,
  low_stock_alerts INTEGER   NOT NULL,
  min_threshold    INTEGER   NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (day, sku_id)
);
CREATE INDEX IF NOT EXISTS idx_iad_day        ON inventory_alerts_daily(day DESC);
CREATE INDEX IF NOT EXISTS idx_iad_sku        ON inventory_alerts_daily(sku_id);

-- ============================================
-- Views úteis para o Streamlit
-- ============================================
CREATE OR REPLACE VIEW v_orders_created_daily AS
SELECT
  day,
  s.name AS supplier,
  total_orders,
  total_qty
FROM orders_created_daily o
JOIN suppliers s ON s.id = o.supplier_id
ORDER BY day DESC, supplier;

CREATE OR REPLACE VIEW v_delays_top_suppliers AS
SELECT
  s.name AS supplier,
  SUM(delayed_orders) AS delayed_events,
  AVG(avg_delay_days) AS avg_delay_days
FROM orders_delayed_daily d
JOIN suppliers s ON s.id = d.supplier_id
GROUP BY s.name
ORDER BY avg_delay_days DESC, delayed_events DESC;

CREATE OR REPLACE VIEW v_inventory_risk AS
SELECT
  day,
  sk.sku_code,
  SUM(low_stock_alerts) AS alerts,
  MIN(min_threshold)    AS min_threshold
FROM inventory_alerts_daily ia
JOIN skus sk ON sk.id = ia.sku_id
GROUP BY day, sk.sku_code
ORDER BY day DESC, alerts DESC;
