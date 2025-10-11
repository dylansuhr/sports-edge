-- Migration 0007: Add indexes for performance optimization
-- Created: 2025-10-10
-- Purpose: Speed up dashboard queries with 100,000+ signals

-- Index for active signals query (signals page)
CREATE INDEX IF NOT EXISTS idx_signals_active_status
ON signals(status, expires_at)
WHERE status = 'active';

-- Index for sorting by edge (most common sort)
CREATE INDEX IF NOT EXISTS idx_signals_edge_desc
ON signals(edge_percent DESC, generated_at DESC)
WHERE status = 'active';

-- Index for filtering by sport
CREATE INDEX IF NOT EXISTS idx_games_sport
ON games(sport);

-- Composite index for CLV queries (performance page)
CREATE INDEX IF NOT EXISTS idx_signals_clv_created
ON signals(created_at DESC, clv_percent)
WHERE clv_percent IS NOT NULL;

-- Index for game time filtering
CREATE INDEX IF NOT EXISTS idx_games_scheduled
ON games(scheduled_at);

-- Analyze tables to update statistics
ANALYZE signals;
ANALYZE games;
ANALYZE markets;

-- Add comments
COMMENT ON INDEX idx_signals_active_status IS 'Speeds up active signal queries on dashboard';
COMMENT ON INDEX idx_signals_edge_desc IS 'Optimizes sorting by edge percentage';
COMMENT ON INDEX idx_signals_clv_created IS 'Speeds up CLV performance queries';
