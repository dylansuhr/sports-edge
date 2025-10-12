-- Migration: Performance Optimization
-- Adds indices for faster query performance on dashboard pages

-- Signals table - optimize common queries
CREATE INDEX IF NOT EXISTS idx_signals_status_expires ON signals(status, expires_at)
  WHERE status = 'active' AND expires_at > NOW();

CREATE INDEX IF NOT EXISTS idx_signals_edge_desc ON signals(edge_percent DESC)
  WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_signals_generated_at ON signals(generated_at DESC);

-- Games table - optimize join performance
CREATE INDEX IF NOT EXISTS idx_games_sport_scheduled ON games(sport, scheduled_at);

CREATE INDEX IF NOT EXISTS idx_games_scheduled_future ON games(scheduled_at)
  WHERE scheduled_at > NOW();

-- Odds snapshots - optimize freshness checks
CREATE INDEX IF NOT EXISTS idx_odds_fetched_at ON odds_snapshots(fetched_at DESC);

-- Paper bets - optimize dashboard queries
CREATE INDEX IF NOT EXISTS idx_paper_bets_status ON paper_bets(status, placed_at DESC);

CREATE INDEX IF NOT EXISTS idx_paper_bets_settled ON paper_bets(settled_at DESC)
  WHERE status != 'pending';

-- Analyze tables to update query planner statistics
ANALYZE signals;
ANALYZE games;
ANALYZE odds_snapshots;
ANALYZE paper_bets;

-- Log completion
DO $$
BEGIN
  RAISE NOTICE 'Performance optimization indices created successfully';
END $$;
