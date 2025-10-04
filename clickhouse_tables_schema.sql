-- ClickHouse Table Schemas for CTA Autonomous Remediation
-- Run these commands in your ClickHouse Cloud console or via clickhouse-client

-- ============================================================================
-- TABLE 1: cta_results
-- Stores all CTA analysis and remediation results
-- ============================================================================
CREATE TABLE IF NOT EXISTS cta_results (
    run_id String,
    timestamp DateTime DEFAULT now(),
    analysis_method String,          -- 'heuristic', 'llm', or 'cached'
    confidence Float32,               -- Confidence score (0.0 to 1.0)
    primary_cause String,             -- Root cause identified
    patch_applied String,             -- JSON string of adapter mapping
    canary_error_rate Float32,        -- Error rate from canary test
    canary_latency_p95 Float32,       -- P95 latency from canary test
    decision String,                  -- 'promote' or 'rollback'
    mttr_seconds Float32,             -- Mean Time To Recovery
    before_error_rate Float32,        -- Error rate before fix
    after_error_rate Float32          -- Error rate after fix
) ENGINE = MergeTree()
ORDER BY (run_id, timestamp)
SETTINGS index_granularity = 8192;

-- Add comment to table
ALTER TABLE cta_results MODIFY COMMENT 'CTA autonomous remediation results and metrics';

-- ============================================================================
-- TABLE 2: trace_events
-- Stores trace events from agent pipeline execution
-- ============================================================================
CREATE TABLE IF NOT EXISTS trace_events (
    run_id String,
    idx UInt32,
    timestamp DateTime DEFAULT now(),
    type String,                      -- 'step', 'tool', 'error', etc.
    payload String                    -- JSON string of full event data
) ENGINE = MergeTree()
ORDER BY (run_id, idx, timestamp)
SETTINGS index_granularity = 8192;

-- Add comment to table
ALTER TABLE trace_events MODIFY COMMENT 'Agent pipeline execution trace events';

-- ============================================================================
-- INDEXES for better query performance
-- ============================================================================

-- Index on decision for filtering promotes vs rollbacks
ALTER TABLE cta_results ADD INDEX idx_decision decision TYPE set(0) GRANULARITY 4;

-- Index on analysis_method for filtering by method type
ALTER TABLE cta_results ADD INDEX idx_method analysis_method TYPE set(0) GRANULARITY 4;

-- Index on event type for filtering trace events
ALTER TABLE trace_events ADD INDEX idx_type type TYPE set(0) GRANULARITY 4;

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Query 1: Get all CTA results for a specific run
-- SELECT * FROM cta_results WHERE run_id = 'your_run_id' ORDER BY timestamp DESC;

-- Query 2: Get promotion success rate
-- SELECT 
--     countIf(decision = 'promote') as promotions,
--     countIf(decision = 'rollback') as rollbacks,
--     promotions / (promotions + rollbacks) * 100 as success_rate
-- FROM cta_results
-- WHERE timestamp >= now() - INTERVAL 24 HOUR;

-- Query 3: Get average MTTR by analysis method
-- SELECT 
--     analysis_method,
--     avg(mttr_seconds) as avg_mttr,
--     count() as incidents
-- FROM cta_results
-- WHERE timestamp >= now() - INTERVAL 7 DAY
-- GROUP BY analysis_method
-- ORDER BY avg_mttr ASC;

-- Query 4: Get before/after error rate improvement
-- SELECT 
--     run_id,
--     before_error_rate,
--     after_error_rate,
--     (before_error_rate - after_error_rate) / before_error_rate * 100 as improvement_pct
-- FROM cta_results
-- WHERE decision = 'promote'
-- ORDER BY timestamp DESC
-- LIMIT 10;

-- Query 5: Get trace events for a specific run
-- SELECT idx, type, timestamp, payload 
-- FROM trace_events 
-- WHERE run_id = 'your_run_id' 
-- ORDER BY idx ASC;

-- Query 6: Get error events across all runs
-- SELECT run_id, idx, timestamp, payload
-- FROM trace_events
-- WHERE type = 'error'
-- ORDER BY timestamp DESC
-- LIMIT 100;

-- ============================================================================
-- MATERIALIZED VIEWS (Optional - for better query performance)
-- ============================================================================

-- View 1: Hourly CTA metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS cta_metrics_hourly
ENGINE = SummingMergeTree()
ORDER BY (hour, analysis_method)
AS SELECT
    toStartOfHour(timestamp) as hour,
    analysis_method,
    count() as total_incidents,
    countIf(decision = 'promote') as promotions,
    countIf(decision = 'rollback') as rollbacks,
    avg(mttr_seconds) as avg_mttr,
    avg(confidence) as avg_confidence,
    avg(before_error_rate - after_error_rate) as avg_improvement
FROM cta_results
GROUP BY hour, analysis_method;

-- View 2: Daily error summary by type
CREATE MATERIALIZED VIEW IF NOT EXISTS error_summary_daily
ENGINE = SummingMergeTree()
ORDER BY (day, type)
AS SELECT
    toStartOfDay(timestamp) as day,
    type,
    count() as error_count,
    uniqExact(run_id) as unique_runs
FROM trace_events
WHERE type = 'error'
GROUP BY day, type;

-- ============================================================================
-- CLEANUP QUERIES (Optional - for managing data retention)
-- ============================================================================

-- Delete old CTA results (older than 90 days)
-- ALTER TABLE cta_results DELETE WHERE timestamp < now() - INTERVAL 90 DAY;

-- Delete old trace events (older than 30 days)
-- ALTER TABLE trace_events DELETE WHERE timestamp < now() - INTERVAL 30 DAY;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check if tables exist
-- SELECT name, engine FROM system.tables WHERE database = currentDatabase() AND name IN ('cta_results', 'trace_events');

-- Check table row counts
-- SELECT 'cta_results' as table, count() as rows FROM cta_results
-- UNION ALL
-- SELECT 'trace_events' as table, count() as rows FROM trace_events;

-- Check recent data
-- SELECT 'cta_results' as table, max(timestamp) as latest FROM cta_results
-- UNION ALL
-- SELECT 'trace_events' as table, max(timestamp) as latest FROM trace_events;

