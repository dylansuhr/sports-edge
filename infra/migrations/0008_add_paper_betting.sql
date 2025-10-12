-- Migration 0008: Add paper betting system
-- Created: 2025-10-11
-- Purpose: AI-powered paper betting with autonomous decision tracking

-- Paper bets table - tracks all AI-placed mock bets
CREATE TABLE IF NOT EXISTS paper_bets (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
  stake NUMERIC(10, 2) NOT NULL,
  odds_american INTEGER NOT NULL,
  odds_decimal NUMERIC(10, 4) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  result VARCHAR(20),
  profit_loss NUMERIC(10, 2),
  placed_at TIMESTAMP NOT NULL DEFAULT NOW(),
  settled_at TIMESTAMP,
  game_id INTEGER NOT NULL REFERENCES games(id),
  market_name VARCHAR(100) NOT NULL,
  selection VARCHAR(100) NOT NULL,
  edge_percent NUMERIC(5, 2) NOT NULL,
  confidence_level VARCHAR(20) NOT NULL,
  CHECK (status IN ('pending', 'won', 'lost', 'push', 'void')),
  CHECK (result IN ('won', 'lost', 'push', 'void'))
);

-- Paper bankroll tracking - maintains running balance and performance metrics
CREATE TABLE IF NOT EXISTS paper_bankroll (
  id SERIAL PRIMARY KEY,
  balance NUMERIC(10, 2) NOT NULL,
  starting_balance NUMERIC(10, 2) NOT NULL,
  total_bets INTEGER NOT NULL DEFAULT 0,
  total_staked NUMERIC(10, 2) NOT NULL DEFAULT 0,
  total_profit_loss NUMERIC(10, 2) NOT NULL DEFAULT 0,
  roi_percent NUMERIC(6, 2) NOT NULL DEFAULT 0,
  win_count INTEGER NOT NULL DEFAULT 0,
  loss_count INTEGER NOT NULL DEFAULT 0,
  push_count INTEGER NOT NULL DEFAULT 0,
  win_rate NUMERIC(5, 2) NOT NULL DEFAULT 0,
  avg_edge NUMERIC(5, 2),
  avg_clv NUMERIC(5, 2),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Paper bet decisions - tracks AI reasoning for placed AND skipped bets
CREATE TABLE IF NOT EXISTS paper_bet_decisions (
  id SERIAL PRIMARY KEY,
  signal_id INTEGER NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
  decision VARCHAR(10) NOT NULL,
  reasoning TEXT NOT NULL,
  confidence_score NUMERIC(3, 2) NOT NULL,
  kelly_stake NUMERIC(10, 2),
  actual_stake NUMERIC(10, 2),
  edge_percent NUMERIC(5, 2) NOT NULL,
  bankroll_at_decision NUMERIC(10, 2) NOT NULL,
  exposure_pct NUMERIC(5, 2) NOT NULL,
  correlation_risk VARCHAR(20),
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  CHECK (decision IN ('place', 'skip')),
  CHECK (confidence_score BETWEEN 0 AND 1),
  CHECK (correlation_risk IN ('low', 'medium', 'high'))
);

-- Paper betting strategy configs - allows A/B testing different strategies
CREATE TABLE IF NOT EXISTS paper_betting_strategies (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  min_edge NUMERIC(5, 2) NOT NULL DEFAULT 3.0,
  min_confidence VARCHAR(20) NOT NULL DEFAULT 'medium',
  max_stake_pct NUMERIC(5, 2) NOT NULL DEFAULT 1.0,
  kelly_fraction NUMERIC(3, 2) NOT NULL DEFAULT 0.25,
  max_exposure_per_game NUMERIC(5, 2) NOT NULL DEFAULT 3.0,
  max_daily_bets INTEGER,
  enabled BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CHECK (min_confidence IN ('low', 'medium', 'high'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_paper_bets_status ON paper_bets(status);
CREATE INDEX IF NOT EXISTS idx_paper_bets_placed_at ON paper_bets(placed_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_bets_signal_id ON paper_bets(signal_id);
CREATE INDEX IF NOT EXISTS idx_paper_bet_decisions_timestamp ON paper_bet_decisions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_paper_bet_decisions_signal_id ON paper_bet_decisions(signal_id);

-- Initialize paper bankroll with $10,000 starting balance
INSERT INTO paper_bankroll (balance, starting_balance)
VALUES (10000.00, 10000.00)
ON CONFLICT DO NOTHING;

-- Create default conservative strategy
INSERT INTO paper_betting_strategies (
  name,
  description,
  min_edge,
  min_confidence,
  max_stake_pct,
  kelly_fraction,
  max_exposure_per_game
)
VALUES (
  'Conservative',
  'Default strategy: 3% edge minimum, medium confidence, quarter-Kelly sizing',
  3.0,
  'medium',
  1.0,
  0.25,
  3.0
)
ON CONFLICT (name) DO NOTHING;

-- Create aggressive strategy for A/B testing
INSERT INTO paper_betting_strategies (
  name,
  description,
  min_edge,
  min_confidence,
  max_stake_pct,
  kelly_fraction,
  max_exposure_per_game,
  enabled
)
VALUES (
  'Aggressive',
  'Higher risk: 2% edge minimum, low confidence accepted, half-Kelly sizing',
  2.0,
  'low',
  2.0,
  0.50,
  5.0,
  false
)
ON CONFLICT (name) DO NOTHING;

-- Comments
COMMENT ON TABLE paper_bets IS 'AI-placed mock bets for system validation';
COMMENT ON TABLE paper_bankroll IS 'Running balance and performance metrics for paper betting';
COMMENT ON TABLE paper_bet_decisions IS 'AI decision log with reasoning for transparency';
COMMENT ON TABLE paper_betting_strategies IS 'Configurable strategies for A/B testing';
COMMENT ON COLUMN paper_bet_decisions.confidence_score IS 'AI confidence 0.0-1.0 based on multiple factors';
COMMENT ON COLUMN paper_bet_decisions.correlation_risk IS 'Risk assessment for correlated bets (same game/team)';
