-- Migration 0014: Add selection tracking to signals and bets
-- Created: 2025-10-12
-- Purpose: Store market side (team/over/under) so settlement & CLV can match correct outcome

ALTER TABLE signals
    ADD COLUMN IF NOT EXISTS selection VARCHAR(150);

COMMENT ON COLUMN signals.selection IS 'Market side captured when the signal was generated (team name, Over/Under, etc.)';

ALTER TABLE bets
    ADD COLUMN IF NOT EXISTS selection VARCHAR(150);

COMMENT ON COLUMN bets.selection IS 'Market side that was wagered (team name, Over/Under, etc.)';

-- Optional helper index when querying by selection (e.g., CLV lookups)
CREATE INDEX IF NOT EXISTS idx_signals_selection ON signals(selection);
