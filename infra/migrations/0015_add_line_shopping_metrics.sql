-- Migration 0015: Track line shopping improvement on signals
-- Created: 2025-10-13
-- Purpose: Persist odds improvement metrics so milestone checks can verify line shopping

ALTER TABLE signals
    ADD COLUMN IF NOT EXISTS odds_improvement_pct DECIMAL(6, 2);

COMMENT ON COLUMN signals.odds_improvement_pct IS 'Percent improvement vs average book odds when line shopping selected this signal';

-- Optional helper index for analytics
CREATE INDEX IF NOT EXISTS idx_signals_odds_improvement
    ON signals(odds_improvement_pct)
    WHERE odds_improvement_pct IS NOT NULL;
