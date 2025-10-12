-- Migration: Add API Usage Tracking
-- Purpose: Track The Odds API credit usage to stay within free tier (500/month)
-- Date: 2025-10-12

-- Table to track each API request
CREATE TABLE IF NOT EXISTS api_usage_log (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,  -- 'theoddsapi'
    endpoint VARCHAR(255) NOT NULL, -- e.g. '/sports/americanfootball_nfl/odds'
    league VARCHAR(10),              -- nfl, nba, nhl
    credits_used INT NOT NULL DEFAULT 1,
    credits_remaining INT,           -- From x-requests-remaining header
    credits_total INT,               -- From x-requests-used header (total for period)
    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_status INT,             -- HTTP status code
    response_message TEXT,           -- Error message if failed
    success BOOLEAN DEFAULT TRUE
);

-- Index for quick lookups
CREATE INDEX idx_api_usage_provider_timestamp ON api_usage_log(provider, request_timestamp DESC);
CREATE INDEX idx_api_usage_success ON api_usage_log(success, request_timestamp DESC);

-- View for monthly usage summary
CREATE OR REPLACE VIEW api_usage_monthly AS
SELECT
    provider,
    DATE_TRUNC('month', request_timestamp) as month,
    COUNT(*) as total_requests,
    SUM(credits_used) as total_credits_used,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_requests,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_requests,
    MAX(credits_remaining) as current_credits_remaining,
    MIN(request_timestamp) as first_request,
    MAX(request_timestamp) as last_request
FROM api_usage_log
GROUP BY provider, DATE_TRUNC('month', request_timestamp)
ORDER BY month DESC;

-- View for current month usage
CREATE OR REPLACE VIEW api_usage_current_month AS
SELECT
    provider,
    COUNT(*) as requests_this_month,
    SUM(credits_used) as credits_used_this_month,
    MAX(credits_remaining) as credits_remaining,
    MAX(credits_total) as credits_total,
    ROUND((SUM(credits_used)::DECIMAL / MAX(credits_total)) * 100, 1) as usage_percent,
    MAX(request_timestamp) as last_request
FROM api_usage_log
WHERE request_timestamp >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
GROUP BY provider;

-- Comment on table
COMMENT ON TABLE api_usage_log IS 'Tracks API usage to monitor quota and prevent exceeding free tier limits';
COMMENT ON VIEW api_usage_current_month IS 'Current month API usage summary for quota monitoring';
