-- Blockchain Indexer Database Schema
-- This schema stores raw blockchain logs and decoded purchase events

-- ============================================
-- Raw Logs Table
-- Stores the raw JSON logs from the blockchain
-- ============================================
CREATE TABLE IF NOT EXISTS raw_logs (
    id SERIAL PRIMARY KEY,
    block_number BIGINT NOT NULL,
    transaction_hash VARCHAR(66) NOT NULL,
    log_index INTEGER NOT NULL,
    contract_address VARCHAR(42) NOT NULL,
    topics JSONB NOT NULL,
    data TEXT,
    block_timestamp TIMESTAMP NOT NULL,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(transaction_hash, log_index)
);

-- Index for efficient querying
CREATE INDEX IF NOT EXISTS idx_raw_logs_block_number ON raw_logs(block_number);
CREATE INDEX IF NOT EXISTS idx_raw_logs_contract_address ON raw_logs(contract_address);
CREATE INDEX IF NOT EXISTS idx_raw_logs_timestamp ON raw_logs(block_timestamp);

-- ============================================
-- Purchases Table
-- Decoded purchase events with structured data
-- ============================================
CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    buyer_address VARCHAR(42) NOT NULL,
    product_id INTEGER NOT NULL,
    price_wei NUMERIC(78, 0) NOT NULL,  -- uint256 max is 78 digits
    quantity INTEGER NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    block_number BIGINT NOT NULL,
    transaction_hash VARCHAR(66) NOT NULL,
    log_index INTEGER NOT NULL,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(transaction_hash, log_index)
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_purchases_buyer ON purchases(buyer_address);
CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(product_id);
CREATE INDEX IF NOT EXISTS idx_purchases_timestamp ON purchases(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_purchases_block ON purchases(block_number);

-- ============================================
-- Product Reference Table
-- Static product information for joins
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_price_wei NUMERIC(78, 0) NOT NULL
);

-- Insert product catalog
INSERT INTO products (product_id, name, base_price_wei) VALUES
    (1, 'Coffee', 1000000000000000),      -- 0.001 ETH
    (2, 'Sandwich', 5000000000000000),    -- 0.005 ETH
    (3, 'Pizza', 10000000000000000),      -- 0.01 ETH
    (4, 'Burger', 8000000000000000),      -- 0.008 ETH
    (5, 'Salad', 6000000000000000)        -- 0.006 ETH
ON CONFLICT (product_id) DO NOTHING;

-- ============================================
-- Analytics Views
-- Pre-computed views for common queries
-- ============================================

-- Daily sales summary
CREATE OR REPLACE VIEW daily_sales AS
SELECT
    DATE(event_timestamp) as sale_date,
    COUNT(*) as total_transactions,
    SUM(quantity) as total_items_sold,
    SUM(price_wei) as total_revenue_wei,
    SUM(price_wei) / 1e18 as total_revenue_eth
FROM purchases
GROUP BY DATE(event_timestamp)
ORDER BY sale_date DESC;

-- Product performance
CREATE OR REPLACE VIEW product_performance AS
SELECT
    p.product_id,
    pr.name as product_name,
    COUNT(*) as purchase_count,
    SUM(p.quantity) as total_quantity,
    SUM(p.price_wei) as total_revenue_wei,
    SUM(p.price_wei) / 1e18 as total_revenue_eth,
    AVG(p.quantity) as avg_quantity_per_purchase
FROM purchases p
JOIN products pr ON p.product_id = pr.product_id
GROUP BY p.product_id, pr.name
ORDER BY total_revenue_wei DESC;

-- Buyer activity
CREATE OR REPLACE VIEW buyer_activity AS
SELECT
    buyer_address,
    COUNT(*) as purchase_count,
    SUM(quantity) as total_items,
    SUM(price_wei) as total_spent_wei,
    SUM(price_wei) / 1e18 as total_spent_eth,
    MIN(event_timestamp) as first_purchase,
    MAX(event_timestamp) as last_purchase
FROM purchases
GROUP BY buyer_address
ORDER BY total_spent_wei DESC;

-- Hourly activity (for time-series charts)
CREATE OR REPLACE VIEW hourly_activity AS
SELECT
    DATE_TRUNC('hour', event_timestamp) as hour,
    COUNT(*) as transactions,
    SUM(quantity) as items_sold,
    SUM(price_wei) / 1e18 as revenue_eth
FROM purchases
GROUP BY DATE_TRUNC('hour', event_timestamp)
ORDER BY hour DESC;

-- ============================================
-- Indexer State Table
-- Tracks indexer progress
-- ============================================
CREATE TABLE IF NOT EXISTS indexer_state (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Useful Functions
-- ============================================

-- Convert wei to ETH
CREATE OR REPLACE FUNCTION wei_to_eth(wei_amount NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    RETURN wei_amount / 1e18;
END;
$$ LANGUAGE plpgsql;

-- Get recent purchases with product names
CREATE OR REPLACE FUNCTION get_recent_purchases(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    purchase_id INTEGER,
    buyer VARCHAR,
    product VARCHAR,
    qty INTEGER,
    price_eth NUMERIC,
    purchase_time TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.buyer_address,
        pr.name,
        p.quantity,
        p.price_wei / 1e18,
        p.event_timestamp
    FROM purchases p
    JOIN products pr ON p.product_id = pr.product_id
    ORDER BY p.event_timestamp DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
