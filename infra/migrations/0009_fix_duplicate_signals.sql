-- Migration 0009: Fix duplicate signals issue
-- Created: 2025-10-11
-- Purpose: Remove duplicate signals and add unique constraint

-- First, delete duplicate signals, keeping only the earliest one per unique combination
DELETE FROM signals
WHERE id NOT IN (
    SELECT MIN(id)
    FROM signals
    GROUP BY game_id, market_id, odds_american, sportsbook
);

-- Add unique constraint to prevent future duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_signals_unique 
ON signals(game_id, market_id, odds_american, sportsbook)
WHERE status = 'active';

-- Comments
COMMENT ON INDEX idx_signals_unique IS 'Prevents duplicate active signals for same game/market/odds/book combination';
