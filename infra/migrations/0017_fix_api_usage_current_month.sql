-- Migration 0017: Fix API usage current month view
-- Purpose: Ensure monitoring reflects the lowest remaining credits so alerts fire correctly
-- Date: 2025-11-11

DROP VIEW IF EXISTS api_usage_current_month;

CREATE OR REPLACE VIEW api_usage_current_month AS
SELECT
    provider,
    COUNT(*) AS requests_this_month,
    SUM(credits_used) AS credits_used_this_month,
    MIN(credits_remaining) AS credits_remaining,  -- use lowest remaining value
    MAX(credits_total) AS credits_total,
    ROUND((SUM(credits_used)::DECIMAL / NULLIF(MAX(credits_total), 0)) * 100, 1) AS usage_percent,
    MAX(request_timestamp) AS last_request
FROM api_usage_log
WHERE request_timestamp >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
GROUP BY provider;

COMMENT ON VIEW api_usage_current_month IS 'Current month API usage summary (uses lowest remaining credits for alerting)';
