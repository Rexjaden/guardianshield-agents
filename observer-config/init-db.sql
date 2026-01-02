-- GuardianShield Observer Database Initialization
-- Create additional databases and users for observer services

-- Create Grafana database and user
CREATE DATABASE grafana;
CREATE USER grafana WITH PASSWORD 'grafana123';
GRANT ALL PRIVILEGES ON DATABASE grafana TO grafana;

-- Create additional indices for performance
\c guardian_analytics;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create performance-optimized indices
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blocks_timestamp_height 
    ON blocks USING btree (timestamp DESC, height DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_from_address_timestamp 
    ON transactions USING btree (from_address, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_to_address_timestamp 
    ON transactions USING btree (to_address, timestamp DESC) 
    WHERE to_address IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_value_desc 
    ON transactions USING btree (value DESC) 
    WHERE value > 0;

-- Partial indices for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_recent 
    ON transactions USING btree (timestamp DESC) 
    WHERE timestamp > NOW() - INTERVAL '7 days';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blocks_recent 
    ON blocks USING btree (timestamp DESC) 
    WHERE timestamp > NOW() - INTERVAL '7 days';

-- GIN indices for JSONB data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contract_events_data_gin 
    ON contract_events USING gin (event_data);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_address_tags_metadata_gin 
    ON address_tags USING gin (metadata);

-- Composite indices for analytics queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_blocks_timestamp_tx_count 
    ON blocks USING btree (timestamp, transaction_count);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contract_events_address_name_timestamp 
    ON contract_events USING btree (contract_address, event_name, timestamp DESC);

-- Set up table partitioning for large tables (blocks and transactions)
-- This would be expanded based on data volume requirements

-- Create a function to automatically create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + INTERVAL '1 month';
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I 
                   FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;

-- Create some utility views for common analytics queries
CREATE OR REPLACE VIEW daily_block_stats AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as block_count,
    SUM(transaction_count) as total_transactions,
    AVG(transaction_count) as avg_transactions_per_block,
    SUM(gas_used) as total_gas_used,
    AVG(gas_used) as avg_gas_per_block
FROM blocks 
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

CREATE OR REPLACE VIEW hourly_transaction_stats AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as transaction_count,
    SUM(value) as total_value,
    AVG(value) as avg_value,
    COUNT(DISTINCT from_address) as unique_senders,
    COUNT(DISTINCT to_address) as unique_recipients
FROM transactions 
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- Create a materialized view for address analytics
CREATE MATERIALIZED VIEW address_activity_summary AS
SELECT 
    address,
    tx_count,
    total_sent,
    total_received,
    first_seen,
    last_seen,
    CASE 
        WHEN tx_count > 10000 THEN 'very_active'
        WHEN tx_count > 1000 THEN 'active' 
        WHEN tx_count > 100 THEN 'moderate'
        ELSE 'low_activity'
    END as activity_level
FROM (
    SELECT 
        addr as address,
        COUNT(*) as tx_count,
        SUM(CASE WHEN addr = from_address THEN value ELSE 0 END) as total_sent,
        SUM(CASE WHEN addr = to_address THEN value ELSE 0 END) as total_received,
        MIN(timestamp) as first_seen,
        MAX(timestamp) as last_seen
    FROM (
        SELECT from_address as addr, value, timestamp FROM transactions
        UNION ALL
        SELECT to_address as addr, value, timestamp FROM transactions WHERE to_address IS NOT NULL
    ) addr_txs
    GROUP BY addr
) addr_stats;

-- Create refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_address_activity_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY address_activity_summary;
END;
$$ LANGUAGE plpgsql;

-- Set up automatic statistics collection
ALTER TABLE blocks SET (autovacuum_analyze_scale_factor = 0.02);
ALTER TABLE transactions SET (autovacuum_analyze_scale_factor = 0.02);
ALTER TABLE contract_events SET (autovacuum_analyze_scale_factor = 0.05);

-- Grant necessary permissions to observer user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO observer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO observer;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO observer;

-- Set default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO observer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO observer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO observer;