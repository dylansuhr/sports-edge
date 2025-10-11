-- Migration: Add raw_implied_probability to signals table
-- This tracks the original bookmaker-implied probability (with vig included)
-- while implied_probability stores the vig-removed fair market probability

ALTER TABLE signals
ADD COLUMN IF NOT EXISTS raw_implied_probability DECIMAL(5, 4);

COMMENT ON COLUMN signals.implied_probability IS 'Vig-removed implied probability from market odds';
COMMENT ON COLUMN signals.raw_implied_probability IS 'Original bookmaker implied probability (includes vig)';
