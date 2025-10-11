-- Migration: Add CLV tracking to signals table
-- Tracks closing line value for each signal to measure model performance

ALTER TABLE signals
ADD COLUMN IF NOT EXISTS closing_odds_american INTEGER,
ADD COLUMN IF NOT EXISTS closing_odds_fetched_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS clv_percent DECIMAL(5, 2);

COMMENT ON COLUMN signals.closing_odds_american IS 'Closing line odds (fetched right before game start)';
COMMENT ON COLUMN signals.closing_odds_fetched_at IS 'When the closing line was captured';
COMMENT ON COLUMN signals.clv_percent IS 'Closing Line Value as percentage (positive = beat the closing line)';

-- Index for CLV analysis
CREATE INDEX IF NOT EXISTS idx_signals_clv ON signals(clv_percent) WHERE clv_percent IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_signals_closing_fetched ON signals(closing_odds_fetched_at DESC);
